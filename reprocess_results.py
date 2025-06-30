# reprocess_results.py
import argparse
import os
from src import results_processing

def main():
    # Argument parser for command line options
    parser = argparse.ArgumentParser(
        description="Re-process existing experiment results to generate new CSV and BD-Rate files."
    )
    parser.add_argument(
        "--results_dir",
        required=True,
        help="Path to the timestamped experiment results directory you want to re-process."
    )
    args = parser.parse_args()

    # Check if the results directory exists
    if not os.path.isdir(args.results_dir):
        print(f"Error: Results directory not found at '{args.results_dir}'")
        return

    try:
        # Call the processing function directly
        print(f"🔬 Re-processing results from: {args.results_dir}")
        results_processing.process_results(args.results_dir)
        print("\n✅ Re-processing completed successfully.")
    except Exception as e:
        print(f"\n❌ An error occurred during results processing: {e}")

if __name__ == "__main__":
    main()