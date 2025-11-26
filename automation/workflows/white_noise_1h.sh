#!/bin/bash

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/venv/bin/activate"

echo "Starting White Noise 1 Hour Workflow..."

# 1. Ensure tasks exist (60 mins)
echo "Step 1: Adding tasks..."
python3 projects/white_noise/idea_generator.py --count 1 --duration 60

# 2. Generate Video
echo "Step 2: Generating video..."
python3 projects/white_noise/main.py --count 1 --mode prod

# 3. Upload Video
echo "Step 3: Uploading video..."
python3 video_uploader/batch_upload.py white_noise --count 1 --privacy public --profile relax

echo "Workflow completed."
