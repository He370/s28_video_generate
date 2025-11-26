#!/bin/bash

# Workflow for History Story (What If)
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/venv/bin/activate"

echo "Starting History Story (What If) Workflow..."

# 1. Generate Idea (What If)
echo "Step 1: Generating idea (What If)..."
python3 projects/history_story/idea_generator.py --count 1 --type what_if

# 2. Generate Video
echo "Step 2: Generating video..."
python3 projects/history_story/main.py --count 1 --mode prod

# 3. Upload Video
echo "Step 3: Uploading video..."
python3 video_uploader/batch_upload.py history_story --count 1 --privacy public

echo "Workflow completed."
