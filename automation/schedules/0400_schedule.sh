#!/bin/bash

# Schedule for 04:00 AM

# Resolve paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PYTHON="$PROJECT_ROOT/venv/bin/python"
RUN_JOB="$PROJECT_ROOT/automation/run_job.py"

echo "==================================================="
echo "Starting 4AM Schedule: $(date)"
echo "==================================================="

# 1. Music Video 1 Hour
echo "[Schedule] Running Music Video (1h)..."
$PYTHON $RUN_JOB --project music_video --command "$PROJECT_ROOT/automation/workflows/music_video_1h.sh"

# 2. Music Video 3 Hours
echo "[Schedule] Running Music Video (3h)..."
$PYTHON $RUN_JOB --project music_video --command "$PROJECT_ROOT/automation/workflows/music_video_3h.sh"

echo "==================================================="
echo "4AM Schedule Completed: $(date)"
echo "==================================================="
