import argparse
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from video_generation_tool import batch_processor
from video_uploader.youtube_uploader import YouTubeUploader

def main():
    parser = argparse.ArgumentParser(description="Batch upload videos to YouTube.")
    parser.add_argument("project_name", help="Name of the project (e.g., today_history)")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to upload")
    parser.add_argument("--privacy", default="private", help="Privacy status (private, public, unlisted)")
    
    args = parser.parse_args()
    
    # Setup paths
    project_dir = os.path.join(os.path.dirname(__file__), "../projects", args.project_name)
    videos_json_path = os.path.join(project_dir, "videos.json")
    
    if not os.path.exists(videos_json_path):
        print(f"Error: Project '{args.project_name}' not found or videos.json missing at {videos_json_path}")
        return

    # Load videos
    videos = batch_processor.load_video_queue(videos_json_path)
    if not videos:
        print("No videos found in queue.")
        return

    # Find generated videos to upload
    to_upload = []
    for video in videos:
        if video.get('status') == 'generated':
            to_upload.append(video)
            if len(to_upload) >= args.count:
                break
    
    if not to_upload:
        print("No 'generated' videos found to upload.")
        return

    print(f"Found {len(to_upload)} video(s) to upload.")

    # Initialize uploader
    # Assuming client_secrets.json is in the video_uploader directory
    secrets_file = os.path.join(os.path.dirname(__file__), "client_secrets.json")
    token_file = os.path.join(os.path.dirname(__file__), "token.pickle")
    
    uploader = YouTubeUploader(client_secrets_file=secrets_file, token_file=token_file)
    
    try:
        uploader.authenticate()
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("Please ensure 'client_secrets.json' is present in the video_uploader directory.")
        return

    # Upload loop
    failed_uploads = 0
    for video in to_upload:
        video_index = video.get('index')
        video_path = video.get('output_path')
        
        # Use generated metadata if available, otherwise fallback
        title = video.get('youtube_title', f"Video {video_index}")
        description = video.get('youtube_description', video.get('description', 'Generated Video'))
        tags = video.get('youtube_tags', ['history'])
        
        # Append disclaimer or tags to description if needed
        description += "\n\n#history #ai #generated"

        if not video_path or not os.path.exists(video_path):
            print(f"Skipping video {video_index}: File not found at {video_path}")
            failed_uploads += 1
            continue

        try:
            print(f"\nUploading Video {video_index}...")
            response = uploader.upload_video(
                file_path=video_path,
                title=title,
                description=description,
                privacy_status=args.privacy,
                tags=tags
            )
            
            if response:
                # Update status
                batch_processor.update_video_status(
                    videos_json_path,
                    video_index,
                    'uploaded',
                    date_uploaded=batch_processor.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    youtube_id=response.get('id')
                )
                print(f"✓ Video {video_index} marked as uploaded.")
                
                # Upload thumbnail (scene_0.png)
                try:
                    video_dir = os.path.dirname(video_path)
                    thumbnail_path = os.path.join(video_dir, "assets", "scene_0.png")
                    
                    if os.path.exists(thumbnail_path):
                        print(f"Found thumbnail: {thumbnail_path}")
                        uploader.upload_thumbnail(response.get('id'), thumbnail_path)
                    else:
                        print(f"No thumbnail found at {thumbnail_path}, skipping.")
                except Exception as thumb_e:
                    print(f"Warning: Failed to upload thumbnail: {thumb_e}")
            
        except Exception as e:
            print(f"✗ Failed to upload video {video_index}: {e}")
            failed_uploads += 1

    if failed_uploads > 0:
        print(f"\n{failed_uploads} uploads failed.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
