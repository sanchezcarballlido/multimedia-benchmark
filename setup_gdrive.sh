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
            mkdir -p "${MOUNT_POINT}"
        fi

        # Mount the rclone remote if not already mounted
        if mount | grep -q "on ${MOUNT_POINT}"; then
            echo "--> Storage is already mounted at ${MOUNT_POINT}."
        else
            echo "--> Mounting '${RCLONE_REMOTE}:' at '${MOUNT_POINT}'..."
            rclone mount "${RCLONE_REMOTE}:" "${MOUNT_POINT}" --vfs-cache-mode writes &
            sleep 2 # Give it a moment to mount
            echo "--> Mount command sent to background. Keep this terminal open."
        fi

        # Ensure local data/ and results/ directories exist
        if [ ! -d "data" ]; then
            echo "--> Creating local data/ directory."
            mkdir -p data
        fi
        if [ ! -d "results" ]; then
            echo "--> Creating local results/ directory."
            mkdir -p results
        fi

        # Create/update symbolic links
        echo "--> Creating symbolic links for 'data' and 'results'..."
        ln -sfn "${MOUNT_POINT}/${REMOTE_DATA_PATH}" data
        ln -sfn "${MOUNT_POINT}/${REMOTE_RESULTS_PATH}" results

        echo "✅ Setup complete. You can now run your experiments in another terminal."
        ;;

    unmount)
        echo "--> Unmounting storage from ${MOUNT_POINT}..."
        fusermount -u "${MOUNT_POINT}"
        echo "✅ Storage unmounted."
        ;;

    *)
        echo "Error: Unknown command '$COMMAND'. Use 'mount' or 'unmount'."
        exit 1
        ;;
esac