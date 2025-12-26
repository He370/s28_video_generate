#!/bin/bash
set -e

# Music Video Generation Workflow via main.py

# Add a new video to queue and process it
./venv/bin/python projects/music_video/main.py --add-new --count 1 --hours ${1:-1}

echo "Done."
