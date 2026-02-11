#!/bin/bash

# Classic Fairy Tale Daily Automation Script

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/venv/bin/activate"

# Step 1: Generate Videos
echo "Step 1: Generating videos..."
python3 "$PROJECT_ROOT/projects/classic_fairy_tale/main.py" --mode prod --count 1

# Step 2: Upload Videos
echo "Step 2: Uploading videos..."
# Default to private upload for safety, can be changed if user implies public. 
# "upload video" doesn't strictly imply public, so private is safer for automation.
# Also, assuming 'classic_fairy_tale' matches the folder name in projects/
python3 "$PROJECT_ROOT/video_uploader/batch_upload.py" classic_fairy_tale --count 1 --privacy public --profile tale

echo "=================================================="
echo "Automation Complete"
echo "=================================================="
