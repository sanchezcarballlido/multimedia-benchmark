# Makefile for the Multimedia Benchmark Framework

# --- Configuration ---
# Default configuration file for experiments. Can be overridden.
# Example: make run CONFIG=configs/another_experiment.yml
CONFIG ?= configs/x264_x265.yml

# Docker image name
IMAGE_NAME = multimedia-benchmark

# --- Phony Targets ---
# Ensures these targets run even if files with the same name exist.
.PHONY: help run reprocess docker-build docker-run docker-reprocess

# --- Help ---
# Default target, prints usage information.
help:
	@echo "Multimedia Benchmark Framework Makefile"
	@echo "--------------------------------------"
	@echo "Usage: make [target]"
	@echo ""
	@echo "Local Targets:"
	@echo "  run             - Runs the full experiment using the default or specified CONFIG."
	@echo "                  - Example: make run CONFIG=configs/my_test.yml"
	@echo "  reprocess       - Re-processes results from an existing experiment directory."
	@echo "                  - Example: make reprocess RESULTS_DIR=results/my_exp_2025-06-30..."
	@echo ""
	@echo "Docker Targets:"
	@echo "  docker-build    - Builds the Docker image '${IMAGE_NAME}'."
	@echo "  docker-run      - Runs the full experiment inside a Docker container."
	@echo "                  - Example: make docker-run CONFIG=configs/my_test.yml"
	@echo "  docker-reprocess- Re-processes results inside a Docker container."
	@echo "                  - Example: make docker-reprocess RESULTS_DIR=results/my_exp_2025-06-30..."

# --- Local Execution Targets ---

# Runs the main experiment script locally.
run:
	@echo "🚀 Running experiment with config: ${CONFIG}"
	python main.py --config ${CONFIG}

# Re-processes the results of a previous experiment locally.
reprocess:
	@if [ -z "${RESULTS_DIR}" ]; then \
		echo "Error: RESULTS_DIR variable is not set."; \
		echo "Usage: make reprocess RESULTS_DIR=/path/to/your/results_folder"; \
		exit 1; \
	fi
	@echo "🔬 Re-processing results from: ${RESULTS_DIR}"
	python reprocess_results.py --results_dir ${RESULTS_DIR}

# --- Docker Execution Targets ---

# Builds the Docker image for the project.
docker-build:
	@echo "🐳 Building Docker image: ${IMAGE_NAME}"
	@docker build -t ${IMAGE_NAME} .

# Runs the main experiment inside a Docker container.
docker-run:
	@echo "🐳 Running experiment in Docker with config: ${CONFIG}"
	@docker run --rm \
		-v $(shell pwd)/results:/app/results \
		-v $(shell pwd)/local_data:/app/data \
		-v $(shell pwd)/${CONFIG}:/app/${CONFIG} \
		${IMAGE_NAME} \
		python main.py --config ${CONFIG}

# Re-processes results of a previous experiment inside a Docker container.
docker-reprocess:
	@if [ -z "${RESULTS_DIR}" ]; then \
		echo "Error: RESULTS_DIR variable is not set."; \
		echo "Usage: make docker-reprocess RESULTS_DIR=results/my_exp_2025-06-30..."; \
		exit 1; \
	fi
	@echo "🔬 Re-processing results from ${RESULTS_DIR} in Docker"
	@docker run --rm \
		-v $(shell pwd)/results:/app/results \
		-v $(shell pwd)/reprocess_results.py:/app/reprocess_results.py \
		${IMAGE_NAME} \
		python reprocess_results.py --results_dir ${RESULTS_DIR}