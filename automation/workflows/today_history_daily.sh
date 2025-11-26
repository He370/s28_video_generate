#!/bin/bash

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/venv/bin/activate"

echo "Starting Today History Daily Workflow..."

# 1. Ensure tasks exist (add next day if needed, though we usually batch add)
# Adding 1 day just in case queue is running low
echo "Step 1: Adding tasks..."
python3 projects/today_history/add_tasks.py --count 1

# 2. Generate Video
echo "Step 2: Generating video..."
python3 projects/today_history/main.py --count 1 --mode prod

# 3. Upload Video
echo "Step 3: Uploading video..."
python3 video_uploader/batch_upload.py today_history --count 1 --privacy public

echo "Workflow completed."
