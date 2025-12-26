#!/bin/bash

# Schedule for 4:00 PM

# Resolve paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PYTHON="$PROJECT_ROOT/venv/bin/python"
RUN_JOB="$PROJECT_ROOT/automation/run_job.py"

echo "==================================================="
echo "Starting 4PM Schedule: $(date)"
echo "==================================================="

# White Noise (8h)
echo "[Schedule] Running White Noise (8h)..."
$PYTHON $RUN_JOB --project white_noise --command "$PROJECT_ROOT/automation/workflows/white_noise_8h.sh"

echo "==================================================="
echo "4PM Schedule Completed: $(date)"
echo "==================================================="
