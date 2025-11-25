import argparse
import os
import sys
import json
from typing import Dict

# Add the project root to sys.path to allow imports from video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool.gemini_client import GeminiClient
from video_generation_tool.script_generator import ScriptGenerator
from video_generation_tool.audio_generator import AudioGenerator
from video_generation_tool.video_maker import VideoMaker
from video_generation_tool.utils import ensure_dir
from video_generation_tool import batch_processor
from video_generation_tool.metadata_generator import MetadataGenerator

def generate_video_for_item(
    video_item: Dict,
    output_base_dir: str,
    client: GeminiClient,
    script_gen: ScriptGenerator,
    audio_gen: AudioGenerator,
    mode: str = "dev"
) -> Dict:
    """
    Generate a history video based on a video item configuration.
    
    Args:
        video_item: Dictionary containing video configuration.
        output_base_dir: Base output directory for all videos.
        client: GeminiClient instance.
        script_gen: ScriptGenerator instance.
        audio_gen: AudioGenerator instance.
        mode: Generation mode ('dev' or 'prod').
        
    Returns:
        Dictionary with 'success' (bool) and 'output_path' or 'error' (str).
    """
    video_index = video_item.get('index')
    date = video_item.get('date', 'Unknown Date')
    events = video_item.get('events', 6)
    debug_scene_limit = video_item.get('debug_scene_limit', None)
    image_style = video_item.get('image_style', 'cinematic, photorealistic')
    language = video_item.get('language', 'English')
    
    # Create video-specific output directory
    video_dir = os.path.join(output_base_dir, f"video_{video_index}")
    ensure_dir(video_dir)
    assets_dir = os.path.join(video_dir, "assets")
    ensure_dir(assets_dir)
    
    print(f"\n{'='*60}")
    print(f"Processing Video {video_index}: {date}")
    print(f"Language: {language}")
    print(f"Output directory: {video_dir}")
    print(f"{'='*60}\n")
    
    try:
        # Initialize AudioGenerator with language
        audio_gen = AudioGenerator(language=language, mode=mode)

        # 1. Generate or Load Script
        script_path = os.path.join(assets_dir, "script.txt")
        
        if os.path.exists(script_path):
            print(f"Loading existing script from {script_path}")
            with open(script_path, "r") as f:
                script = f.read()
        else:
            print("Generating history script...")
            context = f"""
            Create a video script about historical events that happened on {date}. Include {events} significant historical events that occurred on this date throughout history.
            Start with a fun fact to mention up to 3 famous people who were born on this day, then present the events chronologically from oldest to most recent. Each event should mention the year and a brief description.
            """
            
            script = script_gen.generate_script(
                context=context,
                language=language,
                category="History",
                word_limit=80 * (events + 1)
            )
            
            if not script:
                return {"success": False, "error": "Failed to generate script"}
            
            # Save script
            with open(script_path, "w") as f:
                f.write(script)
            print(f"Script saved to {script_path}")
        
        # 2. Process Script into Scenes or Load from segments.json
        segments_log_path = os.path.join(assets_dir, "segments.json")
        
        if os.path.exists(segments_log_path):
            print(f"Loading existing segments from {segments_log_path}")
            with open(segments_log_path, "r") as f:
                segments = json.load(f)
            
            # Apply debug limit if needed
            if debug_scene_limit and len(segments) > debug_scene_limit:
                print(f"DEBUG: Limiting segments from {len(segments)} to {debug_scene_limit}")
                segments = segments[:debug_scene_limit]
        else:
            print("Processing script into scenes...")
            video_title = f"Today in History: {date}"
            # Define history-specific split prompt
            split_prompt = f"""
            I have a video script about historical events. Please split it into logical paragraphs or scenes for video narration.
            Each scene should be a coherent segment suitable for a single image.
            For each scene, extract the year if mentioned (e.g., "1911", "1970").
            
            Script:
            {script}
            
            Output strictly in JSON format as a list of objects:
            [
                {{
                    "text": "Paragraph text...",
                    "year": "1911" or null if no year mentioned
                }},
                ...
            ]
            """

            # Translate title and date if needed
            display_title = video_title
            display_date = date
            if language != "English":
                print(f"Translating title and date to {language}...")
                translation_prompt = f"""
                Translate the following to {language}:
                Title: {video_title}
                Date: {date}
                
                Output strictly in JSON format:
                {{
                    "title": "Translated Title",
                    "date": "Translated Date"
                }}
                """
                try:
                    trans_response = client.generate_text(translation_prompt, response_mime_type="application/json")
                    trans_data = json.loads(trans_response)
                    display_title = trans_data.get("title", video_title)
                    display_date = trans_data.get("date", date)
                    print(f"Translated: {display_title}, {display_date}")
                except Exception as e:
                    print(f"Translation failed: {e}. Using original text.")

            # Define image generator callback
            def history_image_prompt_generator(scene_text: str, index: int, metadata: dict) -> str:
                is_title = (index == 0)
                year = metadata.get("year")
                
                # Prepare text for image prompt with style
                if image_style:
                    styled_text = f"[Style: {image_style}] {scene_text}"
                else:
                    styled_text = scene_text
                
                # Generate base image prompt
                if is_title:
                    # For the title card, ask the model to pick the most attractive scene from the whole script
                    title_prompt_request = f"""
                    Analyze the following video script and identify the most visually striking, dramatic, or attractive historical scene described in it. 
                    Describe this specific scene in great detail to be used as the background image for the video's title card.
                    The description should be purely visual, focusing on the setting, lighting, atmosphere, and key elements.
                    
                    Script:
                    {script}
                    
                    Style: {image_style if image_style else 'cinematic, photorealistic, historical documentary style'}
                    """
                    image_prompt = client.generate_image_prompt(title_prompt_request)
                else:
                    image_prompt = client.generate_image_prompt(styled_text)
                
                # Add text rendering instructions
                if is_title and display_title:
                    text_instruction = f"\n\nIMPORTANT: Create a stunning, cinematic text '{display_title}' centered perfectly in the middle of the composition. The text should be large, elegant, and rendered in a unique, creative font that perfectly embodies the image's art style. The text material and finish (e.g., metallic, stone, glowing, painted) should integrate seamlessly with the visual environment."
                    image_prompt += text_instruction
                elif year and display_date:
                    text_instruction = f"\n\nIMPORTANT: Include bold, clear text displaying the year '{year}' and date '{display_date}' in a font style that matches the {image_style if image_style else 'historical documentary'} aesthetic. The text should be integrated naturally into the composition, clearly readable but not obscuring important visual elements."
                    image_prompt += text_instruction
                
                return image_prompt

            scenes = script_gen.process_script(
                script_text=script,
                split_prompt=split_prompt,
                image_prompt_generator_func=history_image_prompt_generator,
                debug_scene_limit=debug_scene_limit
            )
            
            if not scenes:
                return {"success": False, "error": "Failed to process script"}
            
            # 3. Initialize Segments and Save
            segments = []
            for i, scene in enumerate(scenes):
                if debug_scene_limit and i >= debug_scene_limit:
                    print(f"DEBUG: Limiting scenes from {len(scenes)} to {debug_scene_limit}")
                    break
                
                img_path = os.path.join(assets_dir, f"scene_{i}.png")
                audio_path = os.path.join(assets_dir, f"scene_{i}.mp3")
                
                segment_data = {
                    "image": img_path,
                    "audio": audio_path,
                    "text": scene.get("text", ""),
                    "image_prompt": scene.get("image_prompt", "")
                }
                
                # Add fallback prompt for title card (scene 0)
                if i == 0:
                    fallback_base = f"A cinematic, photorealistic still life composition representing history and time. The scene features antique objects such as an old leather-bound book, a vintage brass hourglass with flowing sand, a quill pen, and an ancient map spread on a dark wooden desk. The lighting is dramatic and warm, coming from a nearby candle or lantern, creating deep shadows and highlights. The atmosphere is mysterious, scholarly, and nostalgic, evoking a sense of the past. [Style: {image_style if image_style else 'historical documentary'}]"
                    if display_title:
                        text_instruction = f"\n\nIMPORTANT: Create a stunning, cinematic title card. Include the text '{display_title}' centered perfectly in the middle of the composition. The text should be large, elegant, and rendered in a unique, creative font that perfectly embodies the '{image_style}' art style. Do not default to standard serif fonts unless appropriate for the style. The text material and finish (e.g., metallic, stone, glowing, painted) should integrate seamlessly with the visual environment. Add decorative elements that fit the theme to frame the text. The background should ensure high contrast and readability. The overall look should be that of a premium, artistic opening title."
                        fallback_base += text_instruction
                    segment_data["fallback_prompt"] = fallback_base
                
                segments.append(segment_data)
            
            # Log segments initially
            with open(segments_log_path, "w") as f:
                json.dump(segments, f, indent=4)
            print(f"Initial segments logged to {segments_log_path}")

        # 4. Generate Assets for Each Segment
        print("Generating assets for segments...")
        import time
        MAX_RETRIES = 3
        RETRY_DELAY = 1  # seconds

        for i, segment in enumerate(segments):
            print(f"Processing Scene {i+1}/{len(segments)}...")
            
            img_path = segment["image"]
            audio_path = segment["audio"]
            image_prompt = segment["image_prompt"]
            fallback_prompt = segment.get("fallback_prompt")
            scene_text = segment["text"]
            
            # Check if image exists, generate if not with retry
            if os.path.exists(img_path):
                print(f"  Image for scene {i} already exists. Skipping image generation.")
            else:
                from video_generation_tool.utils import generate_image_with_retry
                
                # Try standard generation with retries and prompt regeneration
                success = generate_image_with_retry(
                    client=client,
                    image_prompt=image_prompt,
                    output_path=img_path,
                    max_retries=MAX_RETRIES,
                    max_times_gen_new_prompt=2
                )
                
                if not success:
                    # Project-specific fallback logic
                    if fallback_prompt:
                        print(f"  Attempting fallback prompt for scene {i}...")
                        success = generate_image_with_retry(
                            client=client,
                            image_prompt=fallback_prompt,
                            output_path=img_path,
                            max_retries=1,
                            max_times_gen_new_prompt=0
                        )
                        if success:
                            print("  Fallback image generation successful.")
                        else:
                            print("  Fallback image generation failed.")
                    
                    # Special fallback for the last scene (ending): use title image (scene 0)
                    if not success and i == len(segments) - 1:
                        print(f"  Using title image (scene 0) as fallback for ending scene {i}...")
                        title_img_path = segments[0]["image"]
                        if os.path.exists(title_img_path):
                            import shutil
                            try:
                                shutil.copy2(title_img_path, img_path)
                                print("  Successfully copied title image to ending scene.")
                            except Exception as copy_e:
                                print(f"  Failed to copy title image: {copy_e}")
            
            # Check if audio exists, generate if not
            if os.path.exists(audio_path):
                print(f"  Audio for scene {i} already exists. Skipping audio generation.")
            else:
                try:
                    audio_gen.generate_audio_sync(scene_text, audio_path)
                except Exception as e:
                     print(f"  Error generating audio for scene {i}: {e}")
        
        # 4. Create Video
        print("Creating video...")
        video_filename = f"video_{video_index}.mp4"
        video_path = os.path.join(video_dir, video_filename)
        video_maker = VideoMaker(output_file=video_path)
        video_maker.create_video(segments)
        print(f"Video created successfully: {video_path}")
        
        return {"success": True, "output_path": video_path}
        
    except Exception as e:
        error_msg = f"Error generating video: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

def main():
    parser = argparse.ArgumentParser(description="Generate history videos in batch from videos.json.")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--mode", choices=["prod", "dev"], default="dev", help="Mode: 'prod' or 'dev' (default: dev)")
    args = parser.parse_args()

    # Setup paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    output_base_dir = os.path.join(project_dir, "output")
    ensure_dir(output_base_dir)
    
    print(f"{'='*60}")
    print(f"Batch Video Generation - Today in History")
    print(f"Mode: {args.mode}")
    print(f"Videos to generate: {args.count}")
    print(f"{'='*60}\n")
    
    # Load video queue
    videos = batch_processor.load_video_queue(videos_json_path)
    if not videos:
        print("No videos found in queue. Please add videos to videos.json")
        return
    
    # Get pending videos
    pending_videos = batch_processor.get_pending_videos(videos, args.count)
    
    if not pending_videos:
        print("No pending videos found in queue.")
        return
    
    print(f"Found {len(pending_videos)} pending video(s) to process.\n")
    
    # Initialize clients
    try:
        client = GeminiClient(mode=args.mode)
        script_gen = ScriptGenerator(client)
        audio_gen = AudioGenerator(mode=args.mode)
    except ValueError as e:
        print(f"Error initializing clients: {e}")
        return
    
    # Process each video
    success_count = 0
    error_count = 0
    
    for video_item in pending_videos:
        video_index = video_item.get('index')
        
        # Generate video
        result = generate_video_for_item(
            video_item=video_item,
            output_base_dir=output_base_dir,
            client=client,
            script_gen=script_gen,
            audio_gen=audio_gen,
            mode=args.mode
        )
        
        # Initialize metadata generator
        metadata_gen = MetadataGenerator(client)
        
        # Update status
        if result['success']:
            # Generate YouTube metadata
            # Generate YouTube metadata
            youtube_title = ""
            youtube_description = ""
            youtube_tags = []
            
            try:
                video_dir = os.path.dirname(result['output_path'])
                script_path = os.path.join(video_dir, "assets", "script.txt")
                
                if os.path.exists(script_path):
                    with open(script_path, 'r') as f:
                        script_content = f.read()
                    
                    metadata = metadata_gen.generate_metadata(
                        script=script_content,
                        topic=f"History events on {video_item.get('date')}",
                        date=video_item.get('date'),
                        extra_requirements=f"Start the title with topic and date, for example 'Today in History: November 26th, ...'"
                    )
                    
                    youtube_title = metadata.get("title", "")
                    youtube_description = metadata.get("description", "")
                    youtube_tags = metadata.get("tags", [])
                    
                    print(f"Generated Title: {youtube_title}")
                else:
                    print("Script file not found, skipping metadata generation.")
            except Exception as e:
                print(f"Error generating metadata: {e}")

            batch_processor.update_video_status(
                videos_json_path,
                video_index,
                'generated',
                output_path=result['output_path'],
                youtube_title=youtube_title,
                youtube_description=youtube_description,
                youtube_tags=youtube_tags
            )
            success_count += 1
            print(f"✓ Video {video_index} completed successfully\n")
        else:
            batch_processor.update_video_status(
                videos_json_path,
                video_index,
                'error',
                error_message=result.get('error', 'Unknown error')
            )
            error_count += 1
            print(f"✗ Video {video_index} failed: {result.get('error')}\n")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Batch Generation Complete")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")
    print(f"{'='*60}")
    
    if error_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()


