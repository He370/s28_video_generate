import subprocess
import time
import os

projects = [
    ("projects/classic_fairy_tale/output/video_10", "Fairy Tale"),
    ("projects/horror_story/output/video_12", "Horror"),
    ("projects/history_story/output/video_100", "History"),
]

python_path = "./venv/bin/python3"

for video_dir, style in projects:
    print(f"🚀 Starting run for {video_dir} (Style: {style})...")
    cmd = [
        python_path, "-m", "langchain.long2shorts.main",
        "--video-dir", video_dir,
        "--style", style
    ]
    # We run them sequentially here to be safe with rate limits, 
    # but we can start it in the background of the shell.
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Finished {video_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed {video_dir}: {e}")
    
    # Small pause between runs
    time.sleep(5)
