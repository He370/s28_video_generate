import os
import sys
import argparse
from typing import List, Dict

# Add the project root to sys.path to allow imports from video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool import batch_processor

def main():
    parser = argparse.ArgumentParser(description="Generate video placeholders for White Noise project.")
    parser.add_argument("--count", type=int, default=5, help="Number of ideas to generate")
    parser.add_argument("--duration", type=int, default=30, help="Duration in minutes for the videos")
    args = parser.parse_args()
    
    # Setup paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    
    print(f"Adding {args.count} new video placeholders...")
    
    # Add to queue
    added_count = 0
    for _ in range(args.count):
        # Create video item structure with placeholders
        video_item = {
            "topic": "Pending Generation",
            "scene_description": "",
            "art_style": "",
            "duration_minutes": args.duration,
            "status": "pending"
        }
        
        batch_processor.add_video_to_queue(videos_json_path, video_item)
        added_count += 1
        
    print(f"Successfully added {added_count} new video placeholders to videos.json")

if __name__ == "__main__":
    main()
