#!/bin/bash

# Schedule for 2:00 PM

# Resolve paths
PROJECT_ROOT="/Users/leo/Documents/antigravity/s28_video_generate"
PYTHON="$PROJECT_ROOT/venv/bin/python"
RUN_JOB="$PROJECT_ROOT/automation/run_job.py"

echo "==================================================="
echo "Starting 2PM Schedule: $(date)"
echo "==================================================="

# History Story (Mystery)
echo "[Schedule] Running History Story (Mystery)..."
$PYTHON $RUN_JOB --project history_story --command "$PROJECT_ROOT/automation/workflows/history_story_mystery.sh"

echo "==================================================="
echo "2PM Schedule Completed: $(date)"
echo "==================================================="
