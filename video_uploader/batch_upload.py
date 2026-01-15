import argparse
import os
import sys
import json
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from video_generation_tool import batch_processor
from video_uploader.youtube_uploader import YouTubeUploader

def main():
    parser = argparse.ArgumentParser(description="Batch upload videos to YouTube.")
    parser.add_argument("project_name", help="Name of the project (e.g., today_history)")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to upload")
    parser.add_argument("--privacy", default="private", help="Privacy status (private, public, unlisted)")
    parser.add_argument("--profile", default=None, help="Credential profile name (e.g., 'horror' for client_secrets_horror.json)")
    
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

    # Load project metadata for playlists (if applicable)
    playlist_metadata = {}
    metadata_path = os.path.join(project_dir, "playlist.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                playlist_metadata = json.load(f)
        except Exception as e:
            print(f"Error loading playlist.json: {e}")

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
    # Determine credential files based on profile
    base_dir = os.path.dirname(__file__)
    if args.profile:
        secrets_file = os.path.join(base_dir, f"client_secrets_{args.profile}.json")
        token_file = os.path.join(base_dir, f"token_{args.profile}.pickle")
        print(f"Using profile '{args.profile}': {os.path.basename(secrets_file)}")
    else:
        secrets_file = os.path.join(base_dir, "client_secrets.json")
        token_file = os.path.join(base_dir, "token.pickle")
        print("Using default credentials.")

    if not os.path.exists(secrets_file):
        print(f"Error: Client secrets file not found: {secrets_file}")
        return
    
    uploader = YouTubeUploader(client_secrets_file=secrets_file, token_file=token_file)
    
    try:
        uploader.authenticate()
    except Exception as e:
        print(f"Authentication failed: {e}")
        print(f"Please ensure '{os.path.basename(secrets_file)}' is present and valid.")
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
        # Append disclaimer or tags to description if needed
        # description += "\n\n#history #ai #generated"

        if not video_path or not os.path.exists(video_path):
            print(f"Skipping video {video_index}: File not found at {video_path}")
            failed_uploads += 1
            continue

        try:
            print(f"\nUploading Video {video_index}...")
            
            # Determine category ID
            category_id = "22" # Default: People & Blogs
            if args.project_name == "music_video":
                category_id = "10" # Music
            
            # specific scheduling logic
            privacy_status = args.privacy
            publish_at = None
            
            if args.privacy == 'public':
                print("Privacy is public, switching to private and scheduling...")
                privacy_status = 'private'
                
                # Determine schedule time
                # history -> 18:00, horror -> 20:00, music -> 07:00, default -> 18:00
                target_hour = 18
                if "history" in args.project_name.lower():
                    target_hour = 18
                elif "horror" in args.project_name.lower():
                    target_hour = 20
                elif "music" in args.project_name.lower():
                    target_hour = 7
                
                now = datetime.datetime.now().astimezone()
                target_time = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
                
                if target_time < now:
                    target_time += datetime.timedelta(days=1)
                
                publish_at = target_time.isoformat()
                print(f"Scheduled for: {publish_at}")

            response = uploader.upload_video(
                file_path=video_path,
                title=title,
                description=description,
                privacy_status=privacy_status,
                tags=tags,
                category_id=category_id,
                made_for_kids=(args.project_name == 'classic_fairy_tale'),
                publish_at=publish_at
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
                
                # Delete video file if project is white_noise or music_video
                if args.project_name in ["white_noise", "music_video"] and os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                        print(f"Deleted video file: {video_path}")
                    except Exception as e:
                        print(f"Error deleting video file: {e}")
                
                # Upload thumbnail
                try:
                    video_dir = os.path.dirname(video_path)
                    
                    # Check for thumbnail.jpg first (music_video project)
                    thumbnail_path = os.path.join(video_dir, "assets", "thumbnail.jpg")
                    if not os.path.exists(thumbnail_path):
                        # Fall back to scene_0.png (other projects)
                        thumbnail_path = os.path.join(video_dir, "assets", "scene_0.png")
                    
                    if os.path.exists(thumbnail_path):
                        print(f"Found thumbnail: {thumbnail_path}")
                        uploader.upload_thumbnail(response.get('id'), thumbnail_path)
                    else:
                        print(f"No thumbnail found (checked thumbnail.jpg and scene_0.png), skipping.")
                except Exception as thumb_e:
                    print(f"Warning: Failed to upload thumbnail: {thumb_e}")
                    
                # Add to playlist if mapped
                playlist_name = video.get('playlist_name')
                if playlist_name and playlist_name in playlist_metadata:
                    playlist_id = playlist_metadata[playlist_name]
                    if playlist_id:
                        print(f"Adding to playlist for '{playlist_name}'...")
                        uploader.add_video_to_playlist(playlist_id, response.get('id'))
                    else:
                        print(f"No playlist ID configured for '{playlist_name}'. Skipping playlist add.")
            
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
