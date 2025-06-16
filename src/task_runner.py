# src/vaf/task_runner.py
import subprocess
import os

def run_encoding(video, output_dir, codec, crf, preset):
    base_filename = f"{video['name']}_{preset}"
    output_file = os.path.join(output_dir, f"{base_filename}.mp4")
    log_file = os.path.join(output_dir, f"{base_filename}_encoding.log")
    
    command = (
        f"ffmpeg -y -i {video['path']} -c:v {codec} "
        f"-crf {crf} -preset {preset} -threads 4 {output_file}"
    )
    
    try:
        with open(log_file, 'w') as f:
            subprocess.run(command, shell=True, check=True, stdout=f, stderr=subprocess.STDOUT)
        return log_file
    except subprocess.CalledProcessError:
        print(f"    [ERROR] Encoding failed. Check the log: {log_file}")
        return None

def run_vmaf(video, encoded_file_path):
    log_file = encoded_file_path.replace('.mp4', '_vmaf.log')
    
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