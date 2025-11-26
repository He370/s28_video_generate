#!/bin/bash

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"

echo "Starting Horror Story Daily Workflow..."

# 1. Ensure tasks exist
echo "Step 1: Adding tasks..."
python3 projects/horror_story/idea_generator.py --count 1 --mode prod

# 2. Generate Video
echo "Step 2: Generating video..."
python3 projects/horror_story/main.py --count 1 --mode prod

# 3. Upload Video
echo "Step 3: Uploading video..."
python3 video_uploader/batch_upload.py horror_story --count 1 --privacy public --profile horror

echo "Workflow completed."
