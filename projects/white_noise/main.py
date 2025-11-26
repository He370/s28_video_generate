import os
import sys
import json
import argparse
import random
from typing import List, Dict
from moviepy import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool.gemini_client import GeminiClient
from video_generation_tool import batch_processor
from video_generation_tool import utils
from video_generation_tool.metadata_generator import MetadataGenerator

def list_available_sounds(sound_dir: str) -> List[str]:
    """Recursively list all audio files in the directory."""
    sound_files = []
    for root, dirs, files in os.walk(sound_dir):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav')):
                # Store relative path from sound_dir
                rel_path = os.path.relpath(os.path.join(root, file), sound_dir)
                sound_files.append(rel_path)
    return sound_files

def select_sounds(client: GeminiClient, scene_description: str, available_sounds: List[str]) -> List[Dict]:
    """Ask Gemini to select suitable sounds."""
    
    # Limit the list of sounds if it's too long to avoid token limits
    # Assuming filenames are descriptive enough
    sound_list_str = "\n".join(available_sounds)
    
    prompt = f"""
    I am creating a white noise/ambience video.
    
    Scene Description: "{scene_description}"
    
    Available Sound Effects:
    {sound_list_str}
    
    Task:
    Select 3 to 5 sound effects from the list that best match the scene.
    Assign a volume level (0.1 to 1.0) for each sound to create a balanced mix. Background ambience should be louder (0.6-0.8), subtle accents should be quieter (0.1-0.3).
    
    Output strictly in JSON format:
    [
        {{
            "filename": "relative/path/to/sound.mp3",
            "volume": 0.5
        }},
        ...
    ]
    """
    
    try:
        response = client.generate_text(prompt, response_mime_type="application/json")
        selection = json.loads(response)
        
        # Validate selection
        valid_selection = []
        for item in selection:
            if item['filename'] in available_sounds:
                valid_selection.append(item)
            else:
                print(f"Warning: Gemini selected non-existent file: {item['filename']}")
        
        return valid_selection
    except Exception as e:
        print(f"Error selecting sounds: {e}")
        return []

def create_looped_audio(sound_path: str, target_duration: float, volume: float) -> AudioFileClip:
    """Load an audio file and loop it to fill the duration."""
    audio = AudioFileClip(sound_path)
    
    # If audio is shorter than target, loop it
    if audio.duration < target_duration:
        n_loops = int(target_duration / audio.duration) + 1
        # Create a list of clips to concatenate
        clips = [audio] * n_loops
        looped_audio = concatenate_audioclips(clips)
        # Trim to exact duration
        final_audio = looped_audio.subclipped(0, target_duration)
    else:
        final_audio = audio.subclipped(0, target_duration)
        
    return final_audio.with_volume_scaled(volume)

def main():
    parser = argparse.ArgumentParser(description="Generate White Noise video.")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--mode", choices=["prod", "dev"], default="dev", help="Mode: 'prod' or 'dev'")
    args = parser.parse_args()
    
    # Setup paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    output_dir = os.path.join(project_dir, "output")
    sound_dir = os.path.join(project_dir, "../../audio_generater/extracted_sounds")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize client
    try:
        client = GeminiClient(mode=args.mode)
    except ValueError as e:
        print(f"Error initializing Gemini client: {e}")
        return

    # Load queue
    videos = batch_processor.load_video_queue(videos_json_path)
    
    processed_count = 0
    for video in videos:
        if processed_count >= args.count:
            break
            
        if video.get("status") == "pending":
            print(f"\nProcessing video: {video['topic']}")
            
            # Create video specific output folder
            video_index = video.get("index", len(videos)) # Fallback if index missing
            video_output_dir = os.path.join(output_dir, f"video_{video_index}")
            assets_dir = os.path.join(video_output_dir, "assets")
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir)
                
            # Check if segments.json exists
            segments_path = os.path.join(assets_dir, "segments.json")
            existing_segments = {}
            if os.path.exists(segments_path):
                try:
                    with open(segments_path, 'r') as f:
                        existing_segments = json.load(f)
                except Exception as e:
                    print(f"Error loading segments.json: {e}")

            # 1. Generate Image
            print("Step 1: Generating Image...")
            image_prompt = f"{video['scene_description']}, {video['art_style']}"
            image_path = os.path.join(assets_dir, "scene.png")
            
            # Use existing image path if available in segments
            if "image_path" in existing_segments and os.path.exists(existing_segments["image_path"]):
                image_path = existing_segments["image_path"]
                print(f"Using existing image from segments.json: {image_path}")
            elif not os.path.exists(image_path):
                # Use advanced model for better quality
                from video_generation_tool import constants
                success = utils.generate_image_with_retry(
                    client, 
                    image_prompt, 
                    image_path, 
                    model=constants.GEMINI_IMAGE_ADVANCED_MODEL
                )
                if not success:
                    print("Failed to generate image. Skipping.")
                    continue
            else:
                print("Image already exists.")

            # 2. Select Sounds
            print("Step 2: Selecting Sounds...")
            
            # Use existing sounds if available in segments
            if "selected_sounds" in existing_segments:
                selected_sounds = existing_segments["selected_sounds"]
                print(f"Using {len(selected_sounds)} existing sounds from segments.json")
            else:
                available_sounds = list_available_sounds(sound_dir)
                selected_sounds = select_sounds(client, video['scene_description'], available_sounds)
                
                if not selected_sounds:
                    print("No sounds selected. Skipping.")
                    continue
            
            print(f"Selected {len(selected_sounds)} sounds:")
            for s in selected_sounds:
                print(f" - {s['filename']} (vol: {s['volume']})")

            # Save to segments.json
            segments_data = {
                "image_path": image_path,
                "selected_sounds": selected_sounds,
                "scene_description": video['scene_description'],
                "art_style": video['art_style']
            }
            with open(segments_path, 'w') as f:
                json.dump(segments_data, f, indent=4)
            print(f"Saved metadata to {segments_path}")

            # 3. Mix Audio & Create Video
            print("Step 3: Creating Video...")
            duration_sec = video['duration_minutes'] * 60
            
            # For testing/dev, limit duration to 30 seconds if not explicitly prod
            # BUT user requested 30 mins. I will respect the json but maybe warn.
            # Actually, generating 30 mins of video takes a LONG time and disk space.
            # I'll stick to the requested duration but add a dev override if needed.
            if args.mode == "dev":
                print("Dev mode: Limiting duration to 30 seconds.")
                duration_sec = 30
            
            try:
                audio_clips = []
                for sound in selected_sounds:
                    full_path = os.path.join(sound_dir, sound['filename'])
                    if os.path.exists(full_path):
                        clip = create_looped_audio(full_path, duration_sec, sound['volume'])
                        audio_clips.append(clip)
                    else:
                        print(f"Sound file not found: {full_path}")
                
                if not audio_clips:
                    print("No valid audio clips created. Skipping.")
                    continue
                    
                final_audio = CompositeAudioClip(audio_clips)
                final_audio = final_audio.with_volume_scaled(0.6)
                
                # Create Video
                video_clip = ImageClip(image_path).with_duration(duration_sec)
                video_clip = video_clip.with_audio(final_audio)
                
                output_video_path = os.path.join(video_output_dir, f"video_{video['index']}.mp4")
                # High audio bitrate (320k), low video fps (1) and preset (veryslow for better compression)
                video_clip.write_videofile(
                    output_video_path, 
                    fps=1, 
                    codec="libx264", 
                    audio_codec="aac", 
                    audio_bitrate="320k",
                    preset="veryslow",
                    ffmpeg_params=["-crf", "28"] # Higher CRF = lower quality/size. 28 is decent for static image.
                )
                
                # 4. Generate Metadata
                print("Step 4: Generating Metadata...")
                metadata_generator = MetadataGenerator(client)
                metadata = metadata_generator.generate_metadata(
                    script=f"Relaxing white noise video. Scene: {video['scene_description']}",
                    topic=video['topic'],
                    extra_requirements=f"Include '{video['duration_minutes']} Minutes' and 'White Noise Relax Video' in the title. Focus on relaxation, sleep, focus, and white noise keywords.",
                    default_tags=["white noise", "relax", "sleep", "focus", "ambient", "study", "meditation"],
                    default_description=f"Relaxing white noise video: {video['topic']}. Perfect for sleep, study, and focus."
                )
                
                # Update status and metadata in one go
                batch_processor.update_video_status(
                    videos_json_path, 
                    video['index'], 
                    "generated", 
                    output_path=output_video_path,
                    youtube_title=metadata.get("title", ""),
                    youtube_description=metadata.get("description", "") + "\n\n#WhiteNoise #Relax #Sleep #Focus #Ambient",
                    youtube_tags=metadata.get("tags", [])
                )
                print(f"Video status and metadata updated for video {video['index']}")
                
            except Exception as e:
                print(f"Error creating video: {e}")
                import traceback
                traceback.print_exc()
                
                # Update status to error
                batch_processor.update_video_status(
                    videos_json_path,
                    video['index'],
                    "error",
                    error_message=str(e)
                )

if __name__ == "__main__":
    main()
