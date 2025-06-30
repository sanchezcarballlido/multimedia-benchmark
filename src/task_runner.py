# src/task_runner.py
import subprocess
import os

# Maps friendly codec names to GStreamer elements
CODEC_MAP = {
    "libx264": "x264enc",
    "libx265": "x265enc",
    # Add other codecs here, e.g., "av1": "av1enc"
}

# Maps videotestsrc pattern names to their integer IDs for GStreamer
GST_VIDEOTESTSRC_PATTERNS = {
    'smpte': 0, 'snow': 1, 'black': 2, 'white': 3, 'red': 4,
    'green': 5, 'blue': 6, 'ball': 18, 'pinstripe': 13,
    'smpte75': 12, 'zone_plate': 15,
}

def _parse_config_file_to_gst_options(config_path):
    """
    Parses a codec config file (.cfg) and returns a GStreamer options string.
    The file should contain key=value pairs, one per line.
    Lines starting with # or empty lines are ignored.
    """
    if not config_path or not os.path.exists(config_path):
        return ""
    
    options = []
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    options.append(line)
    except IOError as e:
        print(f"    [WARNING] Could not read config file: {config_path}. Error: {e}")
        return ""
    
    return " ".join(options)

def generate_videotestsrc_source(video, output_dir):
    """
    Generates a temporary Y4M source file from GStreamer's videotestsrc.
    This file acts as the reference for encoding and VMAF analysis.
    """
    temp_source_path = os.path.join(output_dir, f"temp_ref_{video['name']}.y4m")
    log_file = os.path.join(output_dir, f"temp_ref_{video['name']}_generation.log")

    pattern_name = video.get('pattern', 'smpte')
    pattern_id = GST_VIDEOTESTSRC_PATTERNS.get(pattern_name)
    if pattern_id is None:
        print(f"    [ERROR] Videotestsrc pattern '{pattern_name}' not supported.")
        return None

    duration = video.get('duration_in_sec', 5)
    framerate = video.get('framerate', 30)
    num_buffers = int(duration * framerate)
    width, height = video['resolution'].split('x')

    # Define raw video format based on config
    video_format = "I420" # Default for 8-bit 4:2:0
    if video.get('bit_depth') == 10:
        if video.get('chroma_subsampling') == "4:2:0":
            video_format = "I420_10LE"
        # Add other formats as needed
    
    # GStreamer pipeline to create the source file
    pipeline = (
        f"gst-launch-1.0 -e videotestsrc pattern={pattern_id} num-buffers={num_buffers} is-live=false ! "
        f"video/x-raw,format={video_format},width={width},height={height},framerate={framerate}/1 ! "
        f"y4menc ! filesink location=\"{temp_source_path}\""
    )
    
    print(f"    - Generating videotestsrc source: {os.path.basename(temp_source_path)}")
    try:
        with open(log_file, 'w') as f:
            subprocess.run(pipeline, shell=True, check=True, stdout=f, stderr=subprocess.STDOUT)
        return temp_source_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"    [ERROR] Failed to generate videotestsrc source. Check log: {log_file}. Error: {e}")
        # Clean up failed file
        if os.path.exists(temp_source_path):
            os.remove(temp_source_path)
        return None

def run_encoding(video, output_dir, codec, crf, preset, config_file=None):
    """
    Runs the encoding task using GStreamer and measures CPU time.
    """
    base_filename = f"{video['name']}_{preset}"
    output_file = os.path.join(output_dir, f"{base_filename}.mp4")
    log_file = os.path.join(output_dir, f"{base_filename}_encoding.log")
    time_log_file = os.path.join(output_dir, f"{base_filename}_time.log")

    codec_element = CODEC_MAP.get(codec)
    if not codec_element:
        print(f"    [ERROR] Codec '{codec}' not supported in GStreamer mapping.")
        return None

    # Get additional options from the config file
    config_options = _parse_config_file_to_gst_options(config_file)

    # Add a targeted debug flag for the encoder element. Level 4 (INFO) should show properties.
    debug_flag = f"--gst-debug={codec_element}:4"

    # GStreamer pipeline definition
    if codec == "libx265":
        encoder_params = f"qp={crf}"
        pipeline = (
            f"gst-launch-1.0 {debug_flag} -e filesrc location=\"{video['path']}\" ! decodebin ! videoconvert ! "
            f"{codec_element} speed-preset={preset} {encoder_params} {config_options} ! h265parse ! "
            f"mp4mux ! filesink location=\"{output_file}\""
        )
    elif codec == "libx264":
        encoder_params = f"qp-max={crf}"
        pipeline = (
            f"gst-launch-1.0 {debug_flag} -e filesrc location=\"{video['path']}\" ! decodebin ! videoconvert ! "
            f"{codec_element} speed-preset={preset} {encoder_params} {config_options} ! "
            f"mp4mux ! filesink location=\"{output_file}\""
        )
    else:
        print(f"    [WARNING] No encoder parameters set for codec '{codec}'. Using defaults. No pipeline will be run.")
        return None

    # Wrap the GStreamer command with /usr/bin/time to measure resource usage.
    # The -v flag provides verbose output, and -o redirects it to our time log file.
    command = f"/usr/bin/time -v -o \"{time_log_file}\" {pipeline}"
    
    try:
        with open(log_file, 'w') as f:
            subprocess.run(command, shell=True, check=True, stdout=f, stderr=subprocess.STDOUT)
        return log_file
    except subprocess.CalledProcessError:
        print(f"    [ERROR] GStreamer encoding failed. Check the log: {log_file}")
        if os.path.exists(time_log_file):
            print(f"            Check time command log for details: {time_log_file}")
        return None
    except FileNotFoundError:
        print("[ERROR] `gst-launch-1.0` or `/usr/bin/time` not found. Are they installed and in your PATH?")
        return None

def run_post_processing(encoded_file_path, output_dir, video_config):
    """
    Runs a post-processing pipeline on the encoded video.
    Currently, this only involves decoding, but can be extended with
    filtering steps like super-resolution, denoising, etc.
    """
    # Step 1: Decode the video back to a raw format (Y4M)
    decoded_file_path = encoded_file_path.replace('.mp4', '_decoded.y4m')
    decode_log_file = encoded_file_path.replace('.mp4', '_decoding.log')

    decode_pipeline = (
        f"gst-launch-1.0 -e filesrc location=\"{encoded_file_path}\" ! decodebin ! "
        f"videoconvert ! y4menc ! filesink location=\"{decoded_file_path}\""
    )
    
    print(f"    - Decoding to raw: {os.path.basename(decoded_file_path)}")
    try:
        with open(decode_log_file, 'w') as f:
            subprocess.run(decode_pipeline, shell=True, check=True, stdout=f, stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"    [ERROR] GStreamer decoding failed. Check log: {decode_log_file}. Error: {e}")
        if os.path.exists(decoded_file_path):
            os.remove(decoded_file_path)
        return None

    # --- Placeholder for Additional Filtering ---
    # The 'decoded_file_path' is now the input for any further processing.
    # For example, you could add a call to a Python script for AI filtering here.
    #
    # Example:
    # if 'filters' in video_config:
    #     filtered_path = run_ai_filter(decoded_file_path, video_config['filters'])
    #     if filtered_path:
    #         return filtered_path # Return the path to the final filtered file
    
    # If no other filters are applied, the decoded file is the final raw file.
    return decoded_file_path


def run_vmaf(video, processed_file_path):
    """
    Runs the VMAF analysis using FFmpeg, comparing a processed file against the original.
    """
    # Determine the base for log file names from the processed file path
    base_name = os.path.basename(processed_file_path)
    if base_name.endswith('_decoded.y4m'):
        log_base_name = base_name.replace('_decoded.y4m', '')
    else:
        # Fallback for original behavior if a non-decoded file is passed
        log_base_name = os.path.splitext(base_name)[0]
    
    output_dir = os.path.dirname(processed_file_path)
    vmaf_xml_log = os.path.join(output_dir, f"{log_base_name}_vmaf.log")
    ffmpeg_stderr_log = os.path.join(output_dir, f"{log_base_name}_ffmpeg_vmaf_stderr.log")

    escaped_vmaf_log_path = vmaf_xml_log.replace('\\', '/').replace(':', '\\:')

    # Use env variable, fallback to default path if missing ---
    model_option = ""
    vmaf_model_path = os.getenv("VMAF_MODEL_PATH")
    default_model_path = "/usr/local/share/vmaf/model/vmaf_v0.6.1.json"
    if vmaf_model_path and os.path.exists(vmaf_model_path):
        print(f"    - Using VMAF model: {vmaf_model_path}")
        escaped_model_path = vmaf_model_path.replace('\\', '/').replace(':', '\\:')
        model_option = f":model='path={escaped_model_path}'"
    elif os.path.exists(default_model_path):
        print(f"    [INFO] VMAF_MODEL_PATH not set or file not found. Using default: {default_model_path}")
        escaped_model_path = default_model_path.replace('\\', '/').replace(':', '\\:')
        model_option = f":model='path={escaped_model_path}'"
    else:
        print("    [WARNING] No VMAF model found. VMAF may fail.")

    command = (
        f"ffmpeg -i \"{processed_file_path}\" -i \"{video['path']}\" "
        f"-lavfi \"[0:v]setpts=PTS-STARTPTS[dist];[1:v]setpts=PTS-STARTPTS[ref];"
        f"[dist][ref]libvmaf=log_path='{escaped_vmaf_log_path}':log_fmt=xml:n_threads=4{model_option}\" "
        f"-f null -"
    )
    try:
        print(f"    - Running VMAF... XML log: {vmaf_xml_log}")
        with open(ffmpeg_stderr_log, 'w') as stderr_f:
            subprocess.run(
                command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=stderr_f
            )
        return vmaf_xml_log
    except subprocess.CalledProcessError:
        print(f"    [ERROR] VMAF calculation failed for '{os.path.basename(processed_file_path)}'.")
        print(f"            Check FFmpeg's error log for details: {ffmpeg_stderr_log}")
        return None
    except FileNotFoundError:
        print("[ERROR] `ffmpeg` not found. Is FFmpeg installed and in your PATH?")
        return None