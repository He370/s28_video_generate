#!/bin/bash

# Schedule for 6:00 PM

# Resolve paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PYTHON="$PROJECT_ROOT/venv/bin/python"
RUN_JOB="$PROJECT_ROOT/automation/run_job.py"

echo "==================================================="
echo "Starting 6PM Schedule: $(date)"
echo "==================================================="

# White Noise (3h)
echo "[Schedule] Running White Noise (3h)..."
$PYTHON $RUN_JOB --project white_noise --command "$PROJECT_ROOT/automation/workflows/white_noise_3h.sh"

echo "==================================================="
echo "6PM Schedule Completed: $(date)"
echo "==================================================="
