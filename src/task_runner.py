# src/task_runner.py
import subprocess
import os

# Maps friendly codec names to GStreamer elements
CODEC_MAP = {
    "libx264": "x264enc",
    "libx265": "x265enc",
    # Add other codecs here, e.g., "av1": "av1enc"
}

def run_encoding(video, output_dir, codec, crf, preset):
    """
    Runs the encoding task using GStreamer.
    """
    base_filename = f"{video['name']}_{preset}"
    output_file = os.path.join(output_dir, f"{base_filename}.mp4")
    log_file = os.path.join(output_dir, f"{base_filename}_encoding.log")

    codec_element = CODEC_MAP.get(codec)
    if not codec_element:
        print(f"    [ERROR] Codec '{codec}' not supported in GStreamer mapping.")
        return None

    # GStreamer command
    if codec == "libx265":
        encoder_params = f"qp={crf}"
        pipeline = (
            f"gst-launch-1.0 -e filesrc location=\"{video['path']}\" ! decodebin ! videoconvert ! "
            f"{codec_element} speed-preset={preset} {encoder_params} ! h265parse ! "
            f"mp4mux ! filesink location=\"{output_file}\""
        )
    elif codec == "libx264":
        encoder_params = f"quantizer={crf}"
        pipeline = (
            f"gst-launch-1.0 -e filesrc location=\"{video['path']}\" ! decodebin ! videoconvert ! "
            f"{codec_element} speed-preset={preset} {encoder_params} ! "
            f"mp4mux ! filesink location=\"{output_file}\""
        )
    else:
        encoder_params = ""
        print(f"    [WARNING] No encoder parameters set for codec '{codec}'. Using defaults. No pipeline will be run.")
        return None

    command = pipeline
    
    try:
        with open(log_file, 'w') as f:
            subprocess.run(command, shell=True, check=True, stdout=f, stderr=subprocess.STDOUT)
        return log_file
    except subprocess.CalledProcessError:
        print(f"    [ERROR] GStreamer encoding failed. Check the log: {log_file}")
        return None
    except FileNotFoundError:
        print("[ERROR] `gst-launch-1.0` not found. Is GStreamer installed and in your PATH?")
        return None


def run_vmaf(video, encoded_file_path):
    """
    Runs the VMAF analysis using FFmpeg, with improved error logging and explicit model path.
    """
    vmaf_xml_log = encoded_file_path.replace('.mp4', '_vmaf.log')
    ffmpeg_stderr_log = encoded_file_path.replace('.mp4', '_ffmpeg_vmaf_stderr.log')

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
        f"ffmpeg -i \"{encoded_file_path}\" -i \"{video['path']}\" "
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
        print(f"    [ERROR] VMAF calculation failed for '{os.path.basename(encoded_file_path)}'.")
        print(f"            Check FFmpeg's error log for details: {ffmpeg_stderr_log}")
        return None
    except FileNotFoundError:
        print("[ERROR] `ffmpeg` not found. Is FFmpeg installed and in your PATH?")
        return None