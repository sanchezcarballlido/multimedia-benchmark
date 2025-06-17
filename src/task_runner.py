# src/vaf/task_runner.py
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

    # Improved GStreamer command for 10-bit Y4M input
    command = (
        f"gst-launch-1.0 -e filesrc location={video['path']} ! decodebin ! videoconvert ! "
        f"{codec_element} speed-preset={preset} quantizer={crf} ! "
        f"mp4mux ! filesink location={output_file}"
    )
    
    try:
        with open(log_file, 'w') as f:
            # GStreamer prints info to stderr, so we redirect it
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
    Runs the VMAF analysis using FFmpeg.
    """
    log_file = encoded_file_path.replace('.mp4', '_vmaf.log')
    
    # FFmpeg command for VMAF calculation
    command = (
        f"ffmpeg -i {encoded_file_path} -i {video['path']} "
        f"-lavfi libvmaf='log_path={log_file}:log_fmt=xml:n_threads=4' -f null -"
    )
    
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return log_file
    except subprocess.CalledProcessError:
        print(f"    [ERROR] VMAF calculation failed. Check the command.")
        return None
    except FileNotFoundError:
        print("[ERROR] `ffmpeg` not found. Is FFmpeg installed and in your PATH?")
        return None