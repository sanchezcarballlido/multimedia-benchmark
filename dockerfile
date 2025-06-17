# ==============================================================================
# Dockerfile for Multimedia Benchmark Framework
# ==============================================================================
# This Dockerfile creates a self-contained environment with GStreamer, FFmpeg,
# and all necessary Python dependencies to run the experiments.
#
# It uses a multi-stage build to keep the final image size optimized.
#
# Stage 1: Builder - Installs all system dependencies and VMAF models.
# Stage 2: Final - Copies built dependencies and application code.
# ==============================================================================

# --- Stage 1: Builder ---
# Use a full Ubuntu image to get access to build tools and libraries
FROM ubuntu:22.04 as builder

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential build tools, system libraries, and multimedia packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-pip \
    python3-venv \
    git \
    wget \
    nasm \
    yasm \
    # GStreamer dependencies
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-good1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    gstreamer1.0-libav \
    # FFmpeg dependencies
    ffmpeg \
    libx264-dev \
    libx265-dev \
    && rm -rf /var/lib/apt/lists/*

# Download and place VMAF models for FFmpeg
# FFmpeg's libvmaf will look for these in a standard location
RUN mkdir -p /usr/local/share/vmaf && \
    wget -P /usr/local/share/vmaf https://github.com/Netflix/vmaf/raw/master/model/vmaf_v0.6.1.json


# --- Stage 2: Final Image ---
# Use a slim Python image for a smaller final footprint
FROM python:3.9-slim

# Copy compiled system libraries and binaries from the builder stage
COPY --from=builder /usr/lib/ /usr/lib/
COPY --from=builder /usr/bin/ /usr/bin/
COPY --from=builder /lib/ /lib/
COPY --from=builder /usr/local/share/vmaf /usr/local/share/vmaf

# Install additional system dependencies for Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libfreetype6-dev \
    libpng-dev \
    libopenblas-dev \
    liblapack-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy Python requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py ./
COPY configs/ ./configs/
COPY notebooks/ ./notebooks/
COPY setup_gdrive.sh ./

# Expose Jupyter Notebook port (optional)
EXPOSE 8888

# Set default command (can be overridden)
CMD ["python", "main.py", "--config", "configs/x264_x265.yml"]
# To run Jupyter, override with:
# docker run -p 8888:8888 <image> jupyter notebook --ip=0.0.0.0 --allow-root --notebook-dir=/app/notebooks
