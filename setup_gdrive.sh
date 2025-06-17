#!/bin/bash

# ==============================================================================
# Cloud Storage Setup for Multimedia Benchmark Framework
# ==============================================================================
#
# A focused script to mount/unmount rclone remotes and set up symbolic links.
#
# Usage:
#   ./setup_cloud_storage.sh mount      - Mounts the remote and creates symlinks.
#   ./setup_cloud_storage.sh unmount    - Unmounts the remote.
#
# ==============================================================================

# --- Configuration ---
# The name of your configured rclone remote (e.g., "gdrive").
RCLONE_REMOTE="gdrive"

# The local directory where the remote will be mounted (inside WSL home).
MOUNT_POINT="${HOME}/gdrive"

# Paths within your cloud storage.
# NOTE: Use forward slashes for paths in shell scripts.
REMOTE_DATA_PATH="Fluendo/R+D+i/Grants/6G-XR/Execution/benchmark/data"
REMOTE_RESULTS_PATH="Fluendo/R+D+i/Grants/6G-XR/Execution/benchmark/results"


# --- Dependency Checks ---
check_dependency() {
    command -v "$1" >/dev/null 2>&1 || { echo "Error: $1 is not installed. Please install it and try again."; exit 1; }
}

check_dependency rclone
check_dependency fusermount


# --- Main Logic ---

COMMAND="$1"

if [ -z "$COMMAND" ]; then
    echo "Error: No command specified. Use 'mount' or 'unmount'."
    exit 1
fi

case "$COMMAND" in
    mount)
        echo "--> Setting up cloud storage..."

        # Create mount point if it doesn't exist
        if [ ! -d "${MOUNT_POINT}" ]; then
            echo "--> Creating mount point: ${MOUNT_POINT}"
            mkdir -p "${MOUNT_POINT}" || { echo "Error: Failed to create mount point."; exit 1; }
        fi

        # Mount the rclone remote if not already mounted
        if mount | grep -q "on ${MOUNT_POINT}"; then
            echo "--> Storage is already mounted at ${MOUNT_POINT}."
        else
            echo "--> Mounting '${RCLONE_REMOTE}:' at '${MOUNT_POINT}'..."
            rclone mount "${RCLONE_REMOTE}:" "${MOUNT_POINT}" --vfs-cache-mode writes &
            sleep 2 # Give it a moment to mount
            if ! mount | grep -q "on ${MOUNT_POINT}"; then
                echo "Error: Mount failed. Please check rclone logs and configuration."; exit 1;
            fi
            echo "--> Mount command sent to background. Keep this terminal open."
        fi

        # Ensure local data/ and results/ directories exist
        if [ ! -d "data" ]; then
            echo "--> Creating local data/ directory."
            mkdir -p data || { echo "Error: Failed to create data/ directory."; exit 1; }
        fi
        if [ ! -d "results" ]; then
            echo "--> Creating local results/ directory."
            mkdir -p results || { echo "Error: Failed to create results/ directory."; exit 1; }
        fi

        # Create/update symbolic links
        echo "--> Creating symbolic links for 'data' and 'results'..."
        ln -sfn "${MOUNT_POINT}/${REMOTE_DATA_PATH}" data || { echo "Error: Failed to create symlink for data."; exit 1; }
        ln -sfn "${MOUNT_POINT}/${REMOTE_RESULTS_PATH}" results || { echo "Error: Failed to create symlink for results."; exit 1; }

        echo "✅ Setup complete. You can now run your experiments in another terminal."
        ;;

    unmount)
        echo "--> Unmounting storage from ${MOUNT_POINT}..."
        if mount | grep -q "on ${MOUNT_POINT}"; then
            fusermount -u "${MOUNT_POINT}" || { echo "Error: Failed to unmount."; exit 1; }
            echo "✅ Storage unmounted."
        else
            echo "--> Nothing is mounted at ${MOUNT_POINT}."
        fi
        ;;

    *)
        echo "Error: Unknown command '$COMMAND'. Use 'mount' or 'unmount'."
        exit 1
        ;;
esac