#!/bin/bash

# Setup initialization variables
configuration_file="src/common/bootstrap/configuration/configuration.json"
secrets_file="env_vars/.env"
docker_compose_file="build/workstation/docker/docker-compose.yml"

current_epoch=$(date +%s)
build_name="build-${current_epoch}"

log_dir="build/workstation/logs"
log_file="${log_dir}/${build_name}.log"
mkdir -p $log_dir

# Check virtual environment, python and pip are setup
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Please activate the virtual environment before running the initialization script."
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo "UV is not installed. Please install uv and try again."
    exit 2
fi

# Install required packages
echo "Installing required packages"

uv sync --all-extras

# Run initialization
echo "Running initialization script in the background. You can find live logs at ${log_file}"

nohup python build/workstation/runner.py \
    --build-name $build_name \
    --log-file $log_file  \
    --configuration-file $configuration_file \
    --secrets-file $secrets_file \
    --docker-compose-file $docker_compose_file \
    --init \
    > $log_file &

nohup_pid=$!
echo "Process ID: $nohup_pid"
