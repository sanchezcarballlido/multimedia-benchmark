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
        
        # Run encoding
        encoding_log = task_runner.run_encoding(video, output_dir, codec, crf, preset)
        if not encoding_log:
            return # Skip if encoding failed

        # Run VMAF
        encoded_file_path = encoding_log.replace('_encoding.log', '.mp4')
        task_runner.run_vmaf(video, encoded_file_path)