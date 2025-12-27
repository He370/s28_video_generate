#!/bin/bash

# Schedule for 10:00 AM

# Resolve paths
PROJECT_ROOT="/Users/leo/Documents/antigravity/s28_video_generate"
PYTHON="$PROJECT_ROOT/venv/bin/python"
RUN_JOB="$PROJECT_ROOT/automation/run_job.py"

echo "==================================================="
echo "Starting 10AM Schedule: $(date)"
echo "==================================================="

# White Noise (1h)
echo "[Schedule] Running White Noise (1h)..."
$PYTHON $RUN_JOB --project white_noise --command "$PROJECT_ROOT/automation/workflows/white_noise_1h.sh"

echo "==================================================="
echo "10AM Schedule Completed: $(date)"
echo "==================================================="
