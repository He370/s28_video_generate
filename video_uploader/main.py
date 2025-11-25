import argparse
import os
from .youtube_uploader import YouTubeUploader

def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--title", help="Video title", default="Uploaded Video")
    parser.add_argument("--description", help="Video description", default="Uploaded via Video Generation Pipeline")
    parser.add_argument("--privacy", help="Privacy status (private, public, unlisted)", default="private")
    
    args = parser.parse_args()
    
    uploader = YouTubeUploader()
    uploader.authenticate()
    uploader.upload_video(args.video_path, args.title, args.description, privacy_status=args.privacy)

if __name__ == "__main__":
    main()
