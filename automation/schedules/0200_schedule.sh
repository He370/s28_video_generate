#!/bin/bash

# Schedule for 2:00 AM
# This script manages the execution of workflows scheduled for the night/early morning.

# Resolve paths
PROJECT_ROOT="/Users/leo/Documents/antigravity/s28_video_generate"
PYTHON="$PROJECT_ROOT/venv/bin/python"
RUN_JOB="$PROJECT_ROOT/automation/run_job.py"

echo "==================================================="
echo "Starting 2AM Schedule: $(date)"
echo "==================================================="

# 1. Horror Story Daily
echo "[Schedule] Running Horror Story Daily..."
$PYTHON $RUN_JOB --project horror_story --command "$PROJECT_ROOT/automation/workflows/horror_story_daily.sh"



echo "==================================================="
echo "2AM Schedule Completed: $(date)"
echo "==================================================="