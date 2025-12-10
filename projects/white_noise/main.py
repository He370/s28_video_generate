import os
import sys
import json
import argparse
import random
import datetime
from typing import List, Dict, Tuple
from moviepy import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool.gemini_client import GeminiClient
from video_generation_tool import batch_processor
from video_generation_tool import utils
from video_generation_tool.metadata_generator import MetadataGenerator
from video_generation_tool.constants import GEMINI_TEXT_ADVANCED_MODEL

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

    return sound_files

def get_used_combinations(output_dir: str, videos_json_path: str, target_duration: int) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Scans output directory for existing segments.json files and returns counts
    of used topics and sounds, filtered by the target duration.
    """
    topic_counts = {}
    sound_counts = {}
    
    if not os.path.exists(output_dir):
        return {}, {}

    # Load videos.json to get topics and durations
    index_map = {} # index -> {topic, duration}
    try:
        with open(videos_json_path, 'r') as f:
            videos_data = json.load(f)
            for v in videos_data:
                idx = v.get('index')
                if idx is not None:
                    index_map[idx] = {
                        'topic': v.get('topic', 'Unknown Topic'),
                        'duration': v.get('duration_minutes', 60)
                    }
    except Exception:
        pass

    # Iterate over video_* directories
    subdirs = [d for d in os.listdir(output_dir) if d.startswith("video_") and os.path.isdir(os.path.join(output_dir, d))]
    
    for item in subdirs:
        try:
            # Extract index from folder name "video_123"
            idx_str = item.split("_")[1]
            idx = int(idx_str)
            video_info = index_map.get(idx)
            
            # If we can't find info, or duration doesn't match, skip
            # We only want to count usage for the SAME duration.
            if not video_info or video_info['duration'] != target_duration:
                continue
                
            topic = video_info['topic']
            if topic and topic != "Pending Generation":
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
        except (IndexError, ValueError):
            continue

        segments_path = os.path.join(output_dir, item, "assets", "segments.json")
        if os.path.exists(segments_path):
            try:
                with open(segments_path, 'r') as f:
                    data = json.load(f)
                    sounds = [s.get("filename", "") for s in data.get("selected_sounds", [])]
                    for s in sounds:
                        if s:
                            sound_counts[s] = sound_counts.get(s, 0) + 1
            except Exception:
                continue
                    
    return topic_counts, sound_counts

def generate_concept_and_select_sounds(client: GeminiClient, available_sounds: List[str], topic_counts: Dict[str, int], sound_counts: Dict[str, int]) -> Dict:
    """
    Generate multiple video concepts and select the best one based on soft limits.
    """
    
    # Format sound list with usage counts
    formatted_sounds = []
    # Sort by usage count (ascending) to encourage using less used sounds
    # But we also want to keep some randomness or alphabetical order so it's not always the same top list?
    # Actually, just sorting by count is good guidance for the LLM.
    
    # Create a list of (sound, count)
    sound_usage = [(s, sound_counts.get(s, 0)) for s in available_sounds]
    # Sort by count
    sound_usage.sort(key=lambda x: x[1])
    
    # Take top 150 least used sounds to keep prompt small, or just all if not too many?
    # The original code limited to 150. Let's keep that limit but prioritize least used.
    
    for sound, count in sound_usage[:150]:
        formatted_sounds.append(f"{sound} (Used {count} times)")
        
    sound_list_str = "\n".join(formatted_sounds)
    
    prompt = f"""
    I have a library of sound effects and I need to create "White Noise" video concepts based on them.
    
    Available Sound Effects (with usage counts):
    {sound_list_str}
    
    Task:
    1. Analyze the sounds and come up with 5 UNIQUE and DISTINCT themes/scenes (e.g., "Rainy Cafe", "Space Station", "Forest Campfire").
    2. For each concept:
       - Create a short Title (Topic).
       - Write a detailed Scene Description.
       - Define an Art Style.
       - Select 2 to 4 sound effects.
       - Assign volumes (0.1-1.0).
    
    Guidelines:
    - PREFER sounds that have been used fewer times (0 or low counts).
    - AVOID sounds that have been used > 5 times unless absolutely critical for the scene.
    - Ensure the 5 concepts are different from each other.
    
    Output strictly in JSON format as a LIST of objects:
    [
        {{
            "topic": "Short Title",
            "scene_description": "Detailed visual description...",
            "art_style": "Art style description...",
            "selected_sounds": [
                {{
                    "filename": "relative/path/to/sound.mp3",
                    "volume": 0.5
                }},
                ...
            ]
        }},
        ...
    ]
    """
    
    # Log the prompt
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt.log")
        with open(log_path, "a") as f:
            f.write(f"\n\n{'='*20} PROMPT {datetime.datetime.now()} {'='*20}\n")
            f.write(prompt)
    except Exception as e:
        print(f"Failed to log prompt: {e}")

    try:
        # Use the advanced model
        response = client.generate_text(
            prompt, 
            response_mime_type="application/json",
            model=GEMINI_TEXT_ADVANCED_MODEL
        )
        candidates = json.loads(response)
        
        if not isinstance(candidates, list):
            candidates = [candidates] # Handle case where it returns single object
            
        print(f"Generated {len(candidates)} candidates. Validating against soft limits...")
        
        best_candidate = None
        lowest_usage_score = float('inf')
        
        for cand in candidates:
            topic = cand.get("topic", "Unknown")
            sounds = [s.get("filename") for s in cand.get("selected_sounds", [])]
            
            # Validate sounds exist
            valid_sounds = [s for s in sounds if s in available_sounds]
            if len(valid_sounds) != len(sounds):
                # Skip if it hallucinates sounds
                continue
                
            # Check Soft Limits
            topic_usage = topic_counts.get(topic, 0)
            
            # Sound usage score: max usage of any single sound in the mix
            current_sound_usages = [sound_counts.get(s, 0) for s in valid_sounds]
            max_sound_usage = max(current_sound_usages) if current_sound_usages else 0
            
            print(f"  - Candidate '{topic}': Topic Used {topic_usage}, Max Sound Used {max_sound_usage}")
            
            # Strict Pass Condition: Topic < 2 AND Max Sound Usage < 5
            if topic_usage < 2 and max_sound_usage < 5:
                print(f"    -> SELECTED (Passes soft limits)")
                cand["selected_sounds"] = [s for s in cand["selected_sounds"] if s["filename"] in available_sounds]
                return cand
            
            # Fallback Score: We want to minimize this
            # Weighted score: Topic usage is bad, High sound usage is bad
            score = (topic_usage * 10) + max_sound_usage
            
            if score < lowest_usage_score:
                lowest_usage_score = score
                best_candidate = cand
        
        if best_candidate:
            print(f"    -> SELECTED FALLBACK (Score {lowest_usage_score})")
            best_candidate["selected_sounds"] = [s for s in best_candidate["selected_sounds"] if s["filename"] in available_sounds]
            return best_candidate
            
        return {}
            
    except Exception as e:
        print(f"Error generating concept and sounds: {e}")
        return {}

def generate_tuned_image_prompt(client: GeminiClient, scene_description: str, art_style: str) -> str:
    """Generate a tuned image prompt for better quality."""
    
    prompt = f"""
    I need a high-quality image generation prompt for a video background.
    
    Scene: {scene_description}
    Style: {art_style}
    
    Task:
    Write a detailed, descriptive prompt optimized for an AI image generator (like Imagen or Midjourney). 
    Include details about lighting, composition, texture, and mood. 
    The image should be wide (16:9) and suitable for a background.
    
    Output only the raw prompt text.
    """
    
    try:
        response = client.generate_text(prompt)
        return response.strip()
    except Exception as e:
        print(f"Error generating tuned prompt: {e}")
        return f"{scene_description}, {art_style}, high quality, 8k, detailed"

def select_sounds(client: GeminiClient, scene_description: str, available_sounds: List[str]) -> List[Dict]:
    """Ask Gemini to select suitable sounds (Fallback/Standalone)."""
    
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
    """
    Load an audio file and loop it to fill the duration.
    Since the source files are preprocessed seamless loops, we can just concatenate them.
    """
    audio = AudioFileClip(sound_path)
    
    if audio.duration >= target_duration:
        return audio.subclipped(0, target_duration).with_volume_scaled(volume)
        
    # Calculate loops needed
    n_loops = int(target_duration / audio.duration) + 1
    clips = [audio] * n_loops
    
    # Concatenate
    final_audio = concatenate_audioclips(clips)
    
    # Trim to exact duration
    final_audio = final_audio.subclipped(0, target_duration)
    
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
    sound_dir = os.path.join(project_dir, "resources")
    
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
            print(f"\nProcessing video index: {video.get('index')}")
            
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
            
            # Variables to hold generated data
            selected_sounds = existing_segments.get("selected_sounds", [])
            
            # Check if we need to generate the concept first
            if video.get("topic") == "Pending Generation" or not video.get("scene_description"):
                print("Generating concept and selecting sounds...")
                available_sounds = list_available_sounds(sound_dir)
                if not available_sounds:
                    print("No sounds available to generate concept. Skipping.")
                    continue
                    
                # Get used combinations (counts) to avoid duplicates for THIS duration
                # We allow reusing topics/sounds if the duration is different (e.g. 30min vs 3h)
                topic_counts, sound_counts = get_used_combinations(output_dir, videos_json_path, video.get('duration_minutes', 60))
                
                # Use the combined function
                concept_result = generate_concept_and_select_sounds(client, available_sounds, topic_counts, sound_counts)
                if not concept_result:
                    print("Failed to generate concept. Skipping.")
                    continue
                
                # Update video object
                video["topic"] = concept_result.get("topic", "Untitled White Noise")
                video["scene_description"] = concept_result.get("scene_description", "")
                video["art_style"] = concept_result.get("art_style", "Digital Art")
                
                # Get the selected sounds from the result
                selected_sounds = concept_result.get("selected_sounds", [])
                
                # Save updated concept to json immediately
                batch_processor.update_video_status(
                    videos_json_path, 
                    video['index'], 
                    "pending", 
                    topic=video["topic"],
                    scene_description=video["scene_description"],
                    art_style=video["art_style"]
                )
                print(f"Concept generated: {video['topic']}")
                print(f"Pre-selected {len(selected_sounds)} sounds.")
                
                # Save pre-selected sounds to segments.json so we don't lose them
                existing_segments["selected_sounds"] = selected_sounds
                with open(segments_path, 'w') as f:
                    json.dump(existing_segments, f, indent=4)

            print(f"Processing video: {video['topic']}")

            # 1. Generate Image
            print("Step 1: Generating Image...")
            
            image_path = os.path.join(assets_dir, "scene.png")
            tuned_prompt = existing_segments.get("tuned_prompt", "")
            
            # Check if image exists
            image_exists = False
            if "image_path" in existing_segments and os.path.exists(existing_segments["image_path"]):
                image_path = existing_segments["image_path"]
                image_exists = True
                print(f"Using existing image from segments.json: {image_path}")
            elif os.path.exists(image_path):
                image_exists = True
                print("Image already exists.")
                
            if not image_exists:
                # Generate tuned prompt only if we need to generate the image
                print("Generating tuned image prompt...")
                tuned_prompt = generate_tuned_image_prompt(client, video['scene_description'], video['art_style'])
                print(f"Tuned Prompt: {tuned_prompt[:100]}...")
                
                # Use advanced model for better quality
                from video_generation_tool import constants
                success = utils.generate_image_with_retry(
                    client, 
                    tuned_prompt, 
                    image_path, 
                    model=constants.GEMINI_IMAGE_ADVANCED_MODEL
                )
                if not success:
                    print("Failed to generate image. Skipping.")
                    continue

            # 2. Select Sounds
            print("Step 2: Selecting Sounds...")
            
            # Use existing sounds if available (either from segments.json or just generated)
            if selected_sounds:
                print(f"Using {len(selected_sounds)} pre-selected sounds.")
            else:
                print("No pre-selected sounds found. Running fallback selection...")
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
                "art_style": video['art_style'],
                "tuned_prompt": tuned_prompt
            }
            with open(segments_path, 'w') as f:
                json.dump(segments_data, f, indent=4)
            print(f"Saved metadata to {segments_path}")

            # 3. Mix Audio & Create Video
            print("Step 3: Creating Video...")
            duration_sec = video['duration_minutes'] * 60
            
            # For testing/dev, limit duration to 30 seconds if not explicitly prod
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
                final_audio = final_audio.with_volume_scaled(0.4)
                
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
                    ffmpeg_params=["-crf", "28"] # Higher CRF = lower quality/size. 28 is decent for static image.
                )
                
                # 4. Generate Metadata
                print("Step 4: Generating Metadata...")
                metadata_generator = MetadataGenerator(client)
                # Format duration string
                duration_mins = video['duration_minutes']
                if duration_mins == 60:
                    duration_str = "1 Hour"
                elif duration_mins == 180:
                    duration_str = "3 Hours"
                elif duration_mins == 120:
                    duration_str = "2 Hours"
                elif duration_mins == 480:
                    duration_str = "8 Hours"
                elif duration_mins == 600:
                    duration_str = "10 Hours"
                else:
                    duration_str = f"{duration_mins} Minutes"

                metadata = metadata_generator.generate_metadata(
                    script=f"Relaxing white noise video. Scene: {video['scene_description']}",
                    topic=video['topic'],
                    extra_requirements=f"STRICTLY START the title with '{duration_str} White Noise'. Example: '{duration_str} White Noise Relax Video - {video['topic']}'.",
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
                
                processed_count += 1
                
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
