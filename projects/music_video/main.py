import os
import sys
import json
import argparse
import logging
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool import batch_processor
from projects.music_video import idea_generator
from projects.music_video import video_looper
from projects.music_video import music_selector
from projects.music_video import audio_assembler
from projects.music_video import final_assembler
from projects.music_video import thumbnail_generator
from projects.music_video import seamless_loop_processor
from projects.music_video import title_overlay

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="Generate Music Video.")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--add-new", action="store_true", help="Add a new pending video to queue if none exist")
    parser.add_argument("--hours", type=int, default=1, help="Duration in hours for new videos")
    parser.add_argument("--dev", action="store_true", help="Enable dev mode (dummy generation)")
    parser.add_argument("--enable-veo", action="store_true", help="Enable Veo for video generation (default: static image loop)")
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    output_dir = os.path.join(project_dir, "output")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize videos.json if not exists
    if not os.path.exists(videos_json_path):
        with open(videos_json_path, 'w') as f:
            json.dump([], f)

    # Add new video if requested
    if args.add_new:
        logging.info("Adding new pending video to queue...")
        batch_processor.add_video_to_queue(videos_json_path, {
            "duration_hours": args.hours,
            "status": "pending"
        })

    videos = batch_processor.load_video_queue(videos_json_path)
    pending_videos = [v for v in videos if v.get('status') == 'pending']
    
    if not pending_videos:
        logging.info("No pending videos found.")
        return
    
    processed_count = 0
    
    # Collect existing titles to avoid duplication
    existing_titles = [v.get('topic') for v in videos if v.get('status') in ['generated', 'uploaded'] and v.get('topic')]
    
    # NEW: Collect recently used genres (last 4 videos) to avoid repetition
    # Sort videos by index or completion date to ensure "recent" means recent
    # Assuming index is sufficient proxy for order
    completed_videos = [v for v in videos if v.get('status') in ['generated', 'uploaded']]
    # Sort by index descending
    completed_videos.sort(key=lambda x: x.get('index', 0), reverse=True)
    
    avoid_genres = []
    # Take last 4
    for v in completed_videos[:4]:
        g = v.get('genre')
        if g:
            avoid_genres.append(g)
            
    # De-duplicate
    avoid_genres = list(set(avoid_genres))
    if avoid_genres:
        logging.info(f"Will soft-avoid the following recently used genres: {avoid_genres}")
    
    for video in pending_videos:
        if processed_count >= args.count:
            break
            
        index = video.get('index')
        logging.info(f"Processing video index: {index}")
        
        # Create video specific output folder
        video_dir = os.path.join(output_dir, f"video_{index}")
        assets_dir = os.path.join(video_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            
        # Define file paths
        idea_file = os.path.join(assets_dir, "idea.json")
        cover_image = os.path.join(assets_dir, "cover.png")
        video_loop = os.path.join(assets_dir, "visuals_loop.mp4")
        selected_tracks = os.path.join(assets_dir, "selected_tracks.json")
        final_audio = os.path.join(assets_dir, "final_audio.mp3")
        final_video = os.path.join(video_dir, "final_video.mp4")
        thumbnail = os.path.join(assets_dir, "thumbnail.jpg")
        seamless_loop = os.path.join(assets_dir, "visuals_loop_seamless.mp4")
        final_video_with_title = os.path.join(video_dir, "final_video_with_title.mp4")
        
        try:
            # Step 1: Idea Generation
            if not os.path.exists(idea_file):
                logging.info("Step 1: Generating Idea...")
                # Pass avoid_genres here
                idea = idea_generator.generate_idea_to_file(idea_file, cover_image, existing_titles=existing_titles, avoid_genres=avoid_genres, dev_mode=args.dev)
                if not idea:
                    raise Exception("Failed to generate idea")
                
                # Add new title to existing list for subsequent iterations
                if idea.get('title'):
                    existing_titles.append(idea.get('title'))
                    
                # Add new genre to avoid list for subsequent iterations in THIS batch
                if idea.get('genre'):
                    avoid_genres.append(idea.get('genre'))

                # Update video topic in queue
                batch_processor.update_video_status(
                    videos_json_path, 
                    index, 
                    "pending", 
                    topic=idea.get('title'),
                    scene_description=idea.get('description'),
                    genre=idea.get('genre'),
                    mood=idea.get('mood'),
                    youtube_title=idea.get('title'),
                    youtube_description=idea.get('description'),
                    youtube_tags=idea.get('tags')
                )
            else:
                logging.info("Idea already generated.")
            
            # Step 1b: Generate Thumbnail
            if not os.path.exists(thumbnail):
                logging.info("Step 1b: Generating Thumbnail...")
                thumbnail_generator.generate_thumbnail(idea_file, cover_image, thumbnail)
                if not os.path.exists(thumbnail):
                    logging.warning("Failed to generate thumbnail, continuing anyway...")
            else:
                logging.info("Thumbnail already exists.")

            # Step 2: Video Loop
            if not os.path.exists(video_loop):
                logging.info("Step 2: Generating Video Loop...")
                video_looper.generate_video_loop(idea_file, video_loop, dev_mode=args.dev, use_veo=args.enable_veo)
                if not os.path.exists(video_loop):
                     raise Exception("Failed to generate video loop")
            else:
                logging.info("Video loop already exists.")
            
            # Step 2b: Create Seamless Loop (only if using Veo)
            if args.enable_veo and not os.path.exists(seamless_loop):
                logging.info("Step 2b: Creating Seamless Loop...")
                seamless_loop_processor.create_seamless_loop(video_loop, seamless_loop)
                if not os.path.exists(seamless_loop):
                    logging.warning("Failed to create seamless loop, using original video loop")
                    seamless_loop = video_loop
            else:
                if args.enable_veo:
                    logging.info("Seamless loop already exists.")
                # Use original video loop if not using Veo
                seamless_loop = video_loop

            # Step 3: Music Selection
            if not os.path.exists(selected_tracks):
                logging.info("Step 3: Selecting Music...")
                duration = video.get('duration_hours', 1)
                music_selector.select_music(idea_file, selected_tracks, duration_hours=duration)
                if not os.path.exists(selected_tracks):
                     raise Exception("Failed to select music")
            else:
                logging.info("Music already selected.")

            # Step 4: Audio Assembly
            if not os.path.exists(final_audio):
                logging.info("Step 4: Assembling Audio...")
                audio_assembler.assemble_audio(selected_tracks, final_audio)
                if not os.path.exists(final_audio):
                     raise Exception("Failed to assemble audio")
            else:
                logging.info("Audio already assembled.")
                
            # Step 5: Final Assembly
            if not os.path.exists(final_video):
                logging.info("Step 5: Assembling Final Video...")
                duration = video.get('duration_hours', 1) # Ensure duration is available here
                final_assembler.assemble_final_video(final_audio, seamless_loop, final_video, duration_hours=duration)
                if not os.path.exists(final_video):
                     raise Exception("Failed to assemble final video")
            else:
                logging.info("Final video already exists.")
            
            # Step 6: Add Title Overlay
            if not os.path.exists(final_video_with_title):
                logging.info("Step 6: Adding Title Overlay...")
                title_overlay.add_title_overlay(idea_file, final_video, final_video_with_title)
                if not os.path.exists(final_video_with_title):
                    logging.warning("Failed to add title overlay, using video without title")
                    final_video_with_title = final_video
            else:
                logging.info("Final video with title already exists.")

            # Success! Update status
            logging.info(f"Video {index} completed successfully!")
            
            # Cleanup intermediate audio
            if os.path.exists(final_audio):
                os.remove(final_audio)
                logging.info(f"Deleted intermediate audio file: {final_audio}")

            batch_processor.update_video_status(
                videos_json_path,
                index,
                "generated",
                output_path=final_video_with_title,
                date_completed=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            processed_count += 1

        except Exception as e:
            logging.error(f"Error processing video {index}: {e}")
            import traceback
            traceback.print_exc()
            batch_processor.update_video_status(
                videos_json_path,
                index,
                "error",
                error_message=str(e)
            )

if __name__ == "__main__":
    main()
