# src/experiment.py
import yaml
import os
from datetime import datetime
from . import task_runner
from . import results_processing

class Experiment:
    def __init__(self, config_path, keep_decoded=False):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.results_dir = os.path.join(
            self.config['output_path'],
            f"{self.config['experiment_name']}_{self.timestamp}"
        )
        os.makedirs(self.results_dir, exist_ok=True)
        print(f"Results will be saved in: {self.results_dir}")
        self.keep_decoded_files = keep_decoded

    def run(self):
        print("🚀 Starting experiment...")
        for video in self.config['source_videos']:
            for task_def in self.config['tasks']:
                presets = task_def.get('preset', 'medium')
                if not isinstance(presets, list):
                    presets = [presets]
                
                config_file = task_def.get('config_file') # Get path to config file

                for preset in presets:
                    for crf in task_def['crf_values']:
                        self._run_single_task(video, task_def, crf, preset, config_file)
        
        print("\n🔬 Processing all results...")
        results_processing.process_results(self.results_dir)

    def _run_single_task(self, video, task_def, crf, preset, config_file=None):
        codec = task_def['codec']
        
        # Create folder structure (now includes video name)
        output_dir = os.path.join(self.results_dir, codec, str(crf), video['resolution_name'], video['name'])
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"  - Task: {video['name']} | {codec} @ CRF {crf} | Preset {preset} | Config: {config_file or 'N/A'}")
        
        original_path = video.get('path')
        temp_source_path = None
        is_videotestsrc = video.get('type') == 'videotestsrc'
        final_raw_path = None  # To keep track of the file to be deleted

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
            encoding_log = task_runner.run_encoding(video, output_dir, codec, crf, preset, config_file)
            if not encoding_log:
                return # Skip if encoding failed
            
            encoded_file_path = encoding_log.replace('_encoding.log', '.mp4')

            # Run the post-processing pipeline (decoding + future filters)
            final_raw_path = task_runner.run_post_processing(encoded_file_path, output_dir, video)
            if not final_raw_path:
                return

            # Run VMAF comparing the original video with the final processed raw file
            task_runner.run_vmaf(video, final_raw_path)

        finally:
            # Clean up the temporary source file if one was created
            if temp_source_path and os.path.exists(temp_source_path):
                print(f"    - Cleaning up temporary source: {os.path.basename(temp_source_path)}")
                os.remove(temp_source_path)

            # Clean up the final raw (decoded) file if it exists and the flag is not set
            if final_raw_path and os.path.exists(final_raw_path) and not self.keep_decoded_files:
                print(f"    - Cleaning up decoded raw file: {os.path.basename(final_raw_path)}")
                os.remove(final_raw_path)
            
            # Restore the original video dictionary state for the next task
            if is_videotestsrc:
                video['path'] = original_path