#!/bin/bash

# Schedule for 12:00 PM

# Resolve paths
PROJECT_ROOT="/Users/leo/Documents/antigravity/s28_video_generate"
PYTHON="$PROJECT_ROOT/venv/bin/python"
RUN_JOB="$PROJECT_ROOT/automation/run_job.py"

echo "==================================================="
echo "Starting 12PM Schedule: $(date)"
echo "==================================================="

# Today History
echo "[Schedule] Running Today History..."
$PYTHON $RUN_JOB --project today_history --command "$PROJECT_ROOT/automation/workflows/today_history_daily.sh"

echo "==================================================="
echo "12PM Schedule Completed: $(date)"
echo "==================================================="
