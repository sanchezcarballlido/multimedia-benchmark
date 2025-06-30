# main.py
import argparse
import os
from src.experiment import Experiment

def main():
    # Argument parser for command line options
    parser = argparse.ArgumentParser(description="Video Analysis Framework")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the experiment configuration file (e.g., configs/my_test.yml)"
    )
    parser.add_argument(
        "--keep-decoded-files",
        action="store_true",
        help="If set, the decoded raw (.y4m) files will not be deleted after VMAF analysis."
    )
    args = parser.parse_args()

    # Check if the configuration file exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found at '{args.config}'")
        return

    try:
        # Create and run the experiment, passing the new flag
        exp = Experiment(config_path=args.config, keep_decoded=args.keep_decoded_files)
        exp.run()
        print("\n✅ Experiment completed successfully.")
    except Exception as e:
        print(f"\n❌ An error occurred during experiment execution: {e}")

if __name__ == "__main__":
    main()