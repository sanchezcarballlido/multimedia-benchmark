# Introduction
The Video Codec Benchmark Framework is an open-source toolkit designed to automate, manage, and analyze the benchmarking of video codecs. It enables researchers, developers, and engineers to systematically compare different codec implementations and configurations using objective quality metrics (such as VMAF, PSNR, SSIM), encoding speed, and BD-Rate.

## Why does it exist?

To provide a reproducible, extensible, and scriptable environment for codec evaluation.
To simplify the process of running large-scale codec tests, collecting results, and visualizing performance trade-offs.
To help users make data-driven decisions when selecting codecs or tuning encoding parameters.

## High-level features:
- **Automated experimentation**: Define experiments in YAML configuration files and run them with a single command.
- **Multiple codecs**: Support for various video codecs (e.g., x264, x265, AV1) and their configurations.
- **Quality metrics**: Integration with VMAF, PSNR, SSIM, and other metrics to evaluate video quality.
- **Encoding speed measurement (latency)**: Track encoding time for each codec and configuration.
- **Encoding CPU time measurement (cpu usage)**: Measure CPU usage during encoding to understand resource consumption.
- **BD-Rate calculation**: Automatically compute BD-Rate to compare codecs based on quality and bitrate.
- **Result visualization**: Jupyter Notebooks for visualizing results, comparing codecs, and analyzing performance trade-offs.

---

# Multimedia Benchmark Framework

This repository contains a framework to automate video encoding experiments and quality metric analysis such as VMAF.

## Project Structure

- **/configs**: Configuration files (`.yml`) that define the experiments.
- **/data**: (Optional) For storing source videos. Ignored by Git.
- **/notebooks**: Jupyter Notebooks for analysis and visualization of results.
- **/results**: Output folder for experiment results (logs, videos, CSVs). Ignored by Git.
- **/src**: Main source code of the framework.
- **main.py**: Entry point to run experiments.
- **requirements.txt**: Project dependencies.


## Installation

---

## Prerequisites

Before you begin, ensure you have the following software installed. Please follow the official installation guides for your specific operating system.

-   [**WSL (Windows Subsystem for Linux)**](https://learn.microsoft.com/en-us/windows/wsl/install) - The recommended environment for running this framework on Windows.
-   [**rclone**](https://rclone.org/install/) - Used to connect to and mount cloud storage.
-   [**FFmpeg**](https://ffmpeg.org/download.html) - The core engine for video encoding and analysis.
-   [**Python 3.8+**](https://www.python.org/downloads/)

---

1.  Clone the repository:
    ```bash
    git clone <REPO_URL>
    cd multimedia-benchmark
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Ensure you have the required video codecs installed on your system:
    - **FFmpeg**: The framework uses FFmpeg for video encoding and decoding. Make sure FFmpeg is installed and accessible in your system's PATH.
    - **VMAF**: Install the VMAF library to compute video quality metrics. Follow the [VMAF installation guide]()
    to set it up correctly.

5. Mount cloud storage:
    This framework is designed to work with large files stored remotely. Run the included script to mount your pre-configured `rclone` remote.
    ```bash
    ./setup_gdrive.sh
    ```
    *This will mount your cloud storage at `~/gdrive` and create the necessary symbolic links. Leave this terminal running.*

## Usage

### 1. Prepare your experiment configuration

Edit or copy the template at `configs/experiment_template.yml` to define your experiment. Specify:
- The source videos to benchmark (update the `path` fields).
- The codecs, CRF values, and presets to test.

Example:
```yaml
experiment_name: "my_experiment"
output_path: "results"
source_videos:
  - path: "/path/to/your/video_1080p.y4m"
    name: "VideoName1"
    resolution: "1920x1080"
    resolution_name: "1080p"
tasks:
  - codec: "libx265"
    crf_values: [22, 28, 34]
    preset: "medium"
  - codec: "libx264"
    crf_values: [21, 24, 28]
    preset: "medium"
```

### 2. Run an experiment

From the project root, run:
```bash
python main.py --config configs/experiment_template.yml
```
Replace the config path with your own YAML file if needed.

### 3. Analyze results

After the experiment, results (logs, encoded videos, and `combined_data.csv`) will be saved in a timestamped folder under `results/`.

To analyze and visualize the results, open the Jupyter notebook at `notebooks/analysis_template.ipynb` and update the path to your generated `combined_data.csv` file.