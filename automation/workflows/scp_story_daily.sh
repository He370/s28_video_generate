#!/bin/bash

# SCP Story Daily Workflow
# Generates and uploads one SCP Foundation style video

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/venv/bin/activate"

echo "Starting SCP Story Daily Workflow..."

# 1. Ensure tasks exist (SCP type)
echo "Step 1: Adding SCP task..."
python3 projects/horror_story/idea_generator.py --count 1 --mode prod --type scp_foundation

# 2. Generate Video
echo "Step 2: Generating video..."
python3 projects/horror_story/main.py --count 1 --mode prod

# 3. Upload Video
echo "Step 3: Uploading video..."
python3 video_uploader/batch_upload.py horror_story --count 1 --privacy public --profile horror

echo "Workflow completed."
