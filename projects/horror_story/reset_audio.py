import json
import os
import glob
import argparse

def reset_audio(video_index=None, all_videos=False):
    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    
    if not os.path.exists(videos_json_path):
        print(f"Error: {videos_json_path} not found.")
        return

    with open(videos_json_path, 'r') as f:
        videos = json.load(f)

    updated_count = 0
    
    for video in videos:
        # Determine if we should process this video
        should_process = False
        if all_videos:
            should_process = True
        elif video_index is not None:
            if video.get('index') == video_index:
                should_process = True
        
        # Only process if status is not already pending (or if we want to force re-generation of pending ones too, but user said update TO pending)
        # Actually, if it's already pending, we might still want to delete mp3s if they exist.
        
        if should_process:
            idx = video.get('index')
            print(f"Processing video {idx}...")
            
            # 1. Remove mp3 files in assets
            # Path construction matches main.py
            video_dir = os.path.join(project_dir, "output", f"video_{idx}")
            assets_dir = os.path.join(video_dir, "assets")
            
            if os.path.exists(assets_dir):
                mp3_files = glob.glob(os.path.join(assets_dir, "*.mp3"))
                if mp3_files:
                    print(f"  Found {len(mp3_files)} mp3 files in {assets_dir}. Deleting...")
                    for mp3 in mp3_files:
                        try:
                            os.remove(mp3)
                            print(f"    Deleted {os.path.basename(mp3)}")
                        except OSError as e:
                            print(f"    Error deleting {os.path.basename(mp3)}: {e}")
                else:
                    print(f"  No mp3 files found in {assets_dir}.")
            else:
                print(f"  Assets directory not found: {assets_dir}")
            
            # 2. Update status to reprocess
            old_status = video.get('status')
            if old_status != 'reprocess':
                video['status'] = 'reprocess'
                # Clear output path and metadata if we are resetting?
                # The user just said "update video status to pending".
                # Usually resetting to pending implies clearing generated fields to avoid confusion, 
                # but main.py overwrites them on success.
                # I'll keep it minimal as requested.
                print(f"  Updated status from '{old_status}' to 'reprocess'.")
                updated_count += 1
            else:
                print("  Status is already 'reprocess'.")
                # Even if pending, we deleted mp3s so it will regenerate.

    if updated_count > 0 or (video_index is not None): # Save if we did anything or tried to target a specific one
        with open(videos_json_path, 'w') as f:
            json.dump(videos, f, indent=4)
        print(f"\nUpdated {updated_count} videos in {videos_json_path}.")
    else:
        print("\nNo videos updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset audio for horror story videos.")
    parser.add_argument("--index", type=int, help="Index of the video to reset")
    parser.add_argument("--all", action="store_true", help="Reset all videos")
    
    args = parser.parse_args()
    
    if not args.index and not args.all:
        print("Please specify --index <number> or --all")
    else:
        reset_audio(video_index=args.index, all_videos=args.all)
