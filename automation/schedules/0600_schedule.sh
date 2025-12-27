#!/bin/bash

# Schedule for 6:00 AM

# Resolve paths
PROJECT_ROOT="/Users/leo/Documents/antigravity/s28_video_generate"
PYTHON="$PROJECT_ROOT/venv/bin/python"
RUN_JOB="$PROJECT_ROOT/automation/run_job.py"

echo "==================================================="
echo "Starting 6AM Schedule: $(date)"
echo "==================================================="

# History Story (What If)
echo "[Schedule] Running History Story (What If)..."
$PYTHON $RUN_JOB --project history_story --command "$PROJECT_ROOT/automation/workflows/history_story_what_if.sh"

echo "==================================================="
echo "6AM Schedule Completed: $(date)"
echo "==================================================="
