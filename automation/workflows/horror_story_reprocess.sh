#!/bin/bash

# Workflow to reprocess horror story videos (regenerate and upload)
# Pre-requisite: User must manually reset audio/status using reset_audio.py

set -e

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Check if index is provided (optional, but good for logging)
# If not provided, it will just process whatever is pending/reprocess in the queue up to the count.
VIDEO_INDEX=$1

# Activate virtual environment
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

cd "$PROJECT_ROOT"

echo "Starting Horror Story Reprocess Workflow..."

# 1. Regenerate Video
# We use a count of 50 to catch multiple if needed, or just 1 if the user only reset 1.
# Since main.py picks up 'pending' and 'reprocess', it will work.
echo "Step 1: Regenerating video(s)..."
python3 projects/horror_story/main.py --count 1 --mode prod

# 2. Upload Video
echo "Step 2: Uploading video(s)..."
# Uploading also checks for status 'generated' (which main.py sets after success).
# We assume the user wants to upload immediately.
python3 video_uploader/batch_upload.py horror_story --count 1 --privacy public --profile horror

echo "Reprocessing workflow completed."
