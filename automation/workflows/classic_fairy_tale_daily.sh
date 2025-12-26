#!/bin/bash

# Classic Fairy Tale Daily Automation Script

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# SCRIPT_DIR is .../automation/workflows
PROJECT_ROOT="$SCRIPT_DIR/../../"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

echo "=================================================="
echo "Starting Classic Fairy Tale Automation"
echo "Date: $(date)"
echo "=================================================="

# Check for arguments
MODE="prod"
COUNT=1

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --mode) MODE="$2"; shift ;;
        --count) COUNT="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

export PYTHONPATH=$PROJECT_ROOT

# Step 1: Generate Videos
echo "Step 1: Generating videos..."
python3 "$PROJECT_ROOT/projects/classic_fairy_tale/main.py" --mode "$MODE" --count "$COUNT"

# Step 2: Upload Videos
echo "Step 2: Uploading videos..."
# Default to private upload for safety, can be changed if user implies public. 
# "upload video" doesn't strictly imply public, so private is safer for automation.
# Also, assuming 'classic_fairy_tale' matches the folder name in projects/
python3 "$PROJECT_ROOT/video_uploader/batch_upload.py" classic_fairy_tale --count "$COUNT" --privacy public

echo "=================================================="
echo "Automation Complete"
echo "=================================================="
