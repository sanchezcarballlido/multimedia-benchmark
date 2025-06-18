# src/vaf/experiment.py
import yaml
import os
from datetime import datetime
from . import task_runner
from . import results_processing

class Experiment:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.results_dir = os.path.join(
            self.config['output_path'],
            f"{self.config['experiment_name']}_{self.timestamp}"
        )
        os.makedirs(self.results_dir, exist_ok=True)
        print(f"Results will be saved in: {self.results_dir}")

    def run(self):
        print("🚀 Starting experiment...")
        for video in self.config['source_videos']:
            for task_def in self.config['tasks']:
                for crf in task_def['crf_values']:
                    self._run_single_task(video, task_def, crf)
        
        print("\n🔬 Processing all results...")
        results_processing.process_results(self.results_dir)

    def _run_single_task(self, video, task_def, crf):
        codec = task_def['codec']
        preset = task_def['preset']
        
        # Create folder structure (now includes video name)
        output_dir = os.path.join(self.results_dir, codec, str(crf), video['resolution_name'], video['name'])
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"  - Task: {video['name']} | {codec} @ CRF {crf} | Preset {preset}")
        
        original_path = video.get('path')
        temp_source_path = None
        is_videotestsrc = video.get('type') == 'videotestsrc'

        try:
            # If the source is videotestsrc, generate it on the fly
            if is_videotestsrc:
                temp_source_path = task_runner.generate_videotestsrc_source(video, output_dir)
                if not temp_source_path:
                    print(f"    [SKIPPING] Failed to generate source for {video['name']}.")
                    return
                video['path'] = temp_source_path

            # Ensure a valid source path exists before proceeding
            if not video.get('path') or not os.path.exists(video['path']):
                print(f"    [SKIPPING] Source path not found or is invalid for {video['name']}: {video.get('path')}")
                return

            # Run encoding
            encoding_log = task_runner.run_encoding(video, output_dir, codec, crf, preset)
            if not encoding_log:
                return # Skip if encoding failed

            # Run VMAF
            encoded_file_path = encoding_log.replace('_encoding.log', '.mp4')
            task_runner.run_vmaf(video, encoded_file_path)

        finally:
            # Clean up the temporary source file if one was created
            if temp_source_path and os.path.exists(temp_source_path):
                print(f"    - Cleaning up temporary source: {os.path.basename(temp_source_path)}")
                os.remove(temp_source_path)
            
            # Restore the original video dictionary state for the next task
            if is_videotestsrc:
                video['path'] = original_path