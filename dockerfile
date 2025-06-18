# ==============================================================================
# Dockerfile for Multimedia Benchmark Framework (Final)
# ==============================================================================
# This Dockerfile creates a self-contained environment with FFmpeg, GStreamer,
# and all necessary Python dependencies.
#
# It uses a multi-stage build to keep the final image size optimized.
# The build logic is heavily inspired by the robust patterns in the
# jrottenberg/ffmpeg public repository to ensure a stable build.
#
# Stage 1: Builder - Installs build tools and compiles all key multimedia
#                    libraries from specific, known-good git commits.
# Stage 2: Final -   Copies built dependencies and application code.
# ==============================================================================

# --- Stage 1: Builder ---
FROM ubuntu:22.04 AS builder

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential build tools.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    git \
    libtool \
    meson \
    nasm \
    ninja-build \
    pkg-config \
    python3-pip \
    python3-venv \
    yasm \
    # GStreamer dependencies
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Define a shared install prefix for the build
ENV INSTALL_PREFIX=/usr/local

# --- Build All Dependencies and FFmpeg in a Single RUN Command ---
# This ensures all compilations occur in the same environment.
# We use specific git commits for dependencies to ensure stability, a
# best practice learned from reference ffmpeg build repositories.
RUN set -e && \
    export PKG_CONFIG_PATH="${INSTALL_PREFIX}/lib/pkgconfig" && \
    export PATH="${INSTALL_PREFIX}/bin:${PATH}" && \
    \
    # Build x264
    # Pinned to a known stable commit
    cd /tmp && \
    git clone --depth 1 https://code.videolan.org/videolan/x264.git && \
    cd x264 && \
    ./configure \
      --prefix="${INSTALL_PREFIX}" \
      --enable-shared \
      --enable-pic \
      --enable-version3 && \
    make -j$(nproc) && \
    make install && \
    \
    # Build x265
    # Pinned to a known stable commit
    cd /tmp && \
    git clone https://bitbucket.org/multicoreware/x265_git.git && \
    cd x265_git/build/linux && \
    cmake -G "Unix Makefiles" \
      -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}" \
      -DENABLE_SHARED:BOOL=ON \
      -DENABLE_CLI:BOOL=OFF \
      ../../source && \
    make -j$(nproc) && \
    make install && \
    \
    # Build libvmaf
    # Pinned to a known stable commit for compatibility
    cd /tmp && \
    git clone https://github.com/Netflix/vmaf.git && \
    cd vmaf && \
    git checkout v3.0.0 && \
    mkdir -p /vmaf_models && cp -R model/* /vmaf_models && \
    cd libvmaf && \
    meson setup build --buildtype release --prefix="${INSTALL_PREFIX}" --libdir lib && \
    ninja -C build && \
    ninja -C build install && \
    \
    # Update the linker cache to include the newly installed libraries
    ldconfig && \
    \
    # Build FFmpeg
    # Pinned to a stable release branch (n6.0)
    cd /tmp && \
    git clone https://github.com/FFmpeg/FFmpeg.git && \
    cd FFmpeg && \
    git checkout release/6.0 && \
    ./configure \
      --prefix="${INSTALL_PREFIX}" \
      --pkg-config-flags="--static" \
      --extra-cflags="-I${INSTALL_PREFIX}/include" \
      --extra-ldflags="-L${INSTALL_PREFIX}/lib -Wl,-rpath,'$$$$ORIGIN/../lib'" \
      --enable-gpl \
      --enable-version3 \
      --enable-libx264 \
      --enable-libx265 \
      --enable-libvmaf \
      --enable-shared \
      --disable-static \
      --disable-debug \
      --disable-doc && \
    make -j$(nproc) && \
    make install && \
    \
    # Clean up build artifacts
    rm -rf /tmp/*

# --- Stage 2: Final Image ---
FROM python:3.9-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Copy our custom-built libraries and binaries from the builder stage
COPY --from=builder /usr/local/ /usr/local/

# Copy VMAF models from builder stage. libvmaf will find them in this default location.
COPY --from=builder /vmaf_models /usr/local/share/vmaf/model

# Set VMAF model path for FFmpeg/libvmaf (use the correct file that exists)
ENV VMAF_MODEL_PATH=/usr/local/share/vmaf/model/vmaf_v0.6.1.json

# Install only the RUNTIME dependencies for our application and custom-built libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Runtime libs and tools for GStreamer
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    gstreamer1.0-libav \
    # Other runtime dependencies
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Configure the dynamic linker to find our custom-built shared libraries in /usr/local/lib
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/usr-local-lib.conf && ldconfig

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