#!/bin/bash

# Workflow for generating and uploading a 1-hour Music Video

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/venv/bin/activate"

echo "Starting Music Video 1 Hour Workflow..."

# 1. Generate Video (Add task + Generate)
# Note: --enable-veo is NOT used by default to save costs/time (uses static image loop).
# Add --enable-veo if dynamic video generation is desired.
echo "Step 1: Generating 1-hour music video..."
python3 projects/music_video/main.py --add-new --count 1 --hours 1

# 2. Upload Video
echo "Step 2: Uploading video..."
# Using 'relax' profile as it mimics white_noise setup, or remove --profile to use default.
python3 video_uploader/batch_upload.py music_video --count 1 --privacy public --profile relax

echo "Workflow completed."
