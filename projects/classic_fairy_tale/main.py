import argparse
import os
import sys
import json
from typing import Dict

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool.gemini_client import GeminiClient
from video_generation_tool.script_generator import ScriptGenerator
from video_generation_tool.audio_generator import AudioGenerator
from video_generation_tool.video_maker import VideoMaker
from video_generation_tool.utils import ensure_dir, generate_image_with_retry
from video_generation_tool import batch_processor
from video_generation_tool.metadata_generator import MetadataGenerator
from video_generation_tool.constants import GEMINI_IMAGE_ADVANCED_MODEL

def generate_video_for_item(
    video_item: Dict,
    output_base_dir: str,
    client: GeminiClient,
    script_gen: ScriptGenerator,
    audio_gen: AudioGenerator,
    mode: str = "dev"
) -> Dict:
    """
    Generate a classic fairy tale video based on a video item configuration.
    """
    video_index = video_item.get('index')
    topic = video_item.get('topic', 'Unknown Topic')
    story_type = video_item.get('type', 'classic_fairy_tale')
    debug_scene_limit = video_item.get('debug_scene_limit', None)
    language = video_item.get('language', 'English')
    
    # Create video-specific output directory
    video_dir = os.path.join(output_base_dir, f"video_{video_index}")
    ensure_dir(video_dir)
    assets_dir = os.path.join(video_dir, "assets")
    ensure_dir(assets_dir)
    
    print(f"\n{'='*60}")
    print(f"Processing Video {video_index}: {topic}")
    print(f"Type: {story_type}")
    print(f"Output directory: {video_dir}")
    print(f"{'='*60}\n")
    
    try:
        # Initialize AudioGenerator with language and fairy tale specific prompt and voices
        fairy_tale_prompt = "Please read the following text at a slightly slower than regular speaking pace, suitable for a fairy tale narration: "
        audio_gen = AudioGenerator(
            language=language, 
            mode=mode, 
            prompt_prefix=fairy_tale_prompt,
            voice_name="Aoede", # Gemini Voice (Noble, Steady, Female)
        )



        # --- Step 0: Load Original Story ---
        original_story_path = video_item.get('original_story_path')
        original_text_content = ""
        
        if original_story_path and os.path.exists(original_story_path):
            print(f"Loading original story from {original_story_path}")
            try:
                with open(original_story_path, 'r', encoding='utf-8') as f:
                    original_text_content = f.read()
            except Exception as e:
                print(f"Error reading original story: {e}")
                return {"success": False, "error": f"Failed to read original story: {e}"}
        else:
            print("Error: Original story path not found or invalid.")
            # For this new workflow, original text is required.
            return {"success": False, "error": "Original story text is required for this workflow."}

        # --- Step 1: Select Art Style ---
        # Load art styles
        project_dir = os.path.dirname(os.path.abspath(__file__))
        art_style_path = os.path.join(project_dir, "art_style.json")
        image_style = None

        if os.path.exists(art_style_path):
            print("Selecting art style...")
            with open(art_style_path, 'r') as f:
                art_styles = json.load(f)
            
            book_name = video_item.get('playlist_name', 'Fairy Tale Collection')
            
            style_prompt = f"""
            I have a fairy tale story. Please select the most appropriate art style from the following list to match the story's tone:
            
            Book: "{book_name}"
            Story: "{topic}"
            
            Available Styles:
            {json.dumps(art_styles, indent=2)}
            
            Return ONLY the name of the key of the selected style (e.g., "Classic Sketch Watercolor").
            """
            selected_style_key = client.generate_text(style_prompt).strip().replace('"', '')
            
            if selected_style_key in art_styles:
                image_style = art_styles[selected_style_key]
                print(f"Selected Art Style: {selected_style_key}")
                print(f"Style Description: {image_style}")
            else:
                print(f"Gemini returned unknown style '{selected_style_key}', falling back to default.")
                image_style = "classic storybook illustration, rich colors, detailed background"
        elif not image_style:
             image_style = "classic storybook illustration, rich colors, detailed background"

        # --- Step 2: Generate Storyboard Script ---
        segments_log_path = os.path.join(assets_dir, "segments.json")
        script_path = os.path.join(assets_dir, "script_storyboard.json") # Saving raw storyboard
        
        scenes = []

        if os.path.exists(segments_log_path):
            print(f"Loading existing segments from {segments_log_path}")
            with open(segments_log_path, "r") as f:
                # We expect the final segments format here
                final_segments = json.load(f)
                # If we are debugging, limit here? 
                # Ideally if segments exist we just use them.
        else:
            if os.path.exists(script_path):
                 print(f"Loading existing storyboard from {script_path}")
                 with open(script_path, "r") as f:
                     scenes = json.load(f)
            else:
                scenes = script_gen.generate_storyboard(
                    original_text=original_text_content,
                    context=f"Story Topic: {topic}"
                )
                if not scenes:
                     return {"success": False, "error": "Failed to generate storyboard scenes"}
                
                # Save raw storyboard
                with open(script_path, "w") as f:
                    json.dump(scenes, f, indent=4)

            # --- Step 3: Add Intro and Outro Scenes ---
            # Intro
            intro_scene = {
                "visual_idea": f"A beautiful title card for the story '{topic}'. Magical book cover or opening scene style.",
                "voiceover": f"{topic}"
            }
            scenes.insert(0, intro_scene)
            
            # Outro
            outro_scene = {
                "visual_idea": "A group image of all the main characters from the story, waving or standing together. Warm and inviting.",
                "voiceover": "The end. Please subscribe, your support means a lot!"
            }
            scenes.append(outro_scene)

            if debug_scene_limit:
                 scenes = scenes[:debug_scene_limit]

            # --- Step 4: Prepare Segments (Data Structure for VideoMaker) ---
            final_segments = []
            
            # Generate Reference Character Sheet (Step 1.5 really, but we do it before asset gen)
            reference_image_path = os.path.join(assets_dir, "reference_character_sheet.png")
            if not os.path.exists(reference_image_path):
                 print("Generating reference character sheet...")
                 ref_prompt = f"""
                 Create a detailed character sheet for the main characters of the fairy tale "{topic}".
                 
                 Style: {image_style}
                 
                 Include full-body designs of the protagonist and antagonist.
                 Ensure consistent clothes/colors.
                 Also write the name of the character next to each character.
                 """
                 success = generate_image_with_retry(
                    client=client,
                    image_prompt=ref_prompt,
                    output_path=reference_image_path,
                    max_retries=3,
                    model=GEMINI_IMAGE_ADVANCED_MODEL
                 )
                 if not success:
                     reference_image_path = None # Proceed without it

            # Process scenes into segments
            for i, scene in enumerate(scenes):
                img_path = os.path.join(assets_dir, f"scene_{i}.png")
                audio_path = os.path.join(assets_dir, f"scene_{i}.mp3")
                
                voiceover = scene.get("voiceover", "")
                visual_idea = scene.get("visual_idea", "")
                
                # Construct Image Prompt
                if i == 0:
                     # Intro Title
                     image_prompt_text = f"Title card for '{topic}'. {visual_idea} Style: {image_style}"
                elif i == len(scenes) - 1:
                     # Outro
                     image_prompt_text = f"Final scene. {visual_idea} Style: {image_style}. Characters matching reference."
                else:
                     image_prompt_text = f"Scene description: {visual_idea}. Style: {image_style}."
                
                # We save the *raw* request or generate a refined one? 
                # The visual_idea is usually descriptive enough, but let's make it a full prompt request if needed.
                # For now, simply appending style is often good enough for the advanced model.
                
                segment_data = {
                    "image": img_path,
                    "audio": audio_path,
                    "text": voiceover,
                    "image_prompt": image_prompt_text,
                    "visual_idea": visual_idea 
                }
                final_segments.append(segment_data)

            # Save segments
            with open(segments_log_path, "w") as f:
                json.dump(final_segments, f, indent=4)
            print(f"Segments logged to {segments_log_path}")

        # --- Step 5: Generate Assets (Image and Audio) ---
        print("Generating assets for segments...")
        MAX_RETRIES = 3
        
        # Determine reference image path again for scope
        reference_image_path = os.path.join(assets_dir, "reference_character_sheet.png")
        if not os.path.exists(reference_image_path):
            reference_image_path = None

        for i, segment in enumerate(final_segments):
            print(f"Processing Scene {i+1}/{len(final_segments)}...")
            
            img_path = segment["image"]
            audio_path = segment["audio"]
            image_prompt = segment["image_prompt"]
            scene_text = segment["text"]
            
            # Image
            if os.path.exists(img_path):
                print(f"  Image exists.")
            else:
                # Use advanced model for first and last? Or all? 
                # Let's say all for quality in this project.
                model_to_use = GEMINI_IMAGE_ADVANCED_MODEL 
                
                # Use reference for all except maybe title if it's purely text (but title usually benefits too)
                # But strictly speaking, title/outro might differ.
                # Intro (i=0): Maybe no reference if it's just a book cover.
                # Outro (last): Definitely reference.
                ref_image_to_pass = reference_image_path if (i > 0 and reference_image_path) else None
                
                success = generate_image_with_retry(
                    client=client,
                    image_prompt=image_prompt,
                    output_path=img_path,
                    max_retries=MAX_RETRIES,
                    max_times_gen_new_prompt=1,
                    model=model_to_use,
                    reference_image_path=ref_image_to_pass
                )
                
                if not success:
                     print(f"  Failed to generate image for scene {i}")

            # Audio
            if os.path.exists(audio_path):
                print(f"  Audio exists.")
            else:
                try:
                    if scene_text.strip():
                        # Pass slower rate for Edge TTS (Dev mode)
                        audio_gen.generate_audio_sync(scene_text, audio_path)
                    else:
                        # Create silent audio if text is empty (rare)
                        pass  
                except Exception as e:
                     print(f"  Error generating audio: {e}")

        # --- Step 6: Create Video ---
        print("Creating video...")
        video_filename = f"video_{video_index}.mp4"
        video_path = os.path.join(video_dir, video_filename)
        video_maker = VideoMaker(output_file=video_path)
        # Custom padding for fairy tales: 2s start, 3s end
        padding_config = {0: 2.0, -1: 3.0, 'default': 0.5}
        
        video_maker.create_video(final_segments, padding_config=padding_config)
        print(f"Video created successfully: {video_path}")
        
        return {"success": True, "output_path": video_path}

    except Exception as e:
        error_msg = f"Error generating video: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

def main():
    parser = argparse.ArgumentParser(description="Generate classic fairy tale videos.")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--mode", choices=["prod", "dev"], default="dev", help="Mode: 'prod' or 'dev'")
    args = parser.parse_args()

    # Setup paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    output_base_dir = os.path.join(project_dir, "output")
    ensure_dir(output_base_dir)
    
    print(f"{'='*60}")
    print(f"Batch Video Generation - Classic Fairy Tale")
    print(f"Mode: {args.mode}")
    print(f"{'='*60}\n")
    
    # Load video queue
    videos = batch_processor.load_video_queue(videos_json_path)
    pending_videos = batch_processor.get_pending_videos(videos, args.count)
    
    if not pending_videos:
        print("No pending videos found. Run crawl_stories.py first.")
        return
    
    # Initialize clients
    try:
        client = GeminiClient(mode=args.mode)
        script_gen = ScriptGenerator(client)
        audio_gen = AudioGenerator(mode=args.mode) # Default init
        metadata_gen = MetadataGenerator(client)
    except ValueError as e:
        print(f"Error initializing clients: {e}")
        return
    
    # Process
    for video_item in pending_videos:
        result = generate_video_for_item(
            video_item=video_item,
            output_base_dir=output_base_dir,
            client=client,
            script_gen=script_gen,
            audio_gen=audio_gen,
            mode=args.mode
        )
        
        if result['success']:
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
                        topic=video_item.get('topic'),
                        style="Fairy Tale"
                    )
                    
                    youtube_title = metadata.get("title", "")
                    youtube_description = metadata.get("description", "")
                    youtube_tags = metadata.get("tags", [])
                    
                    project_hashtags = "\n\n#FairyTale #ClassicStories #Storytime"
                    youtube_description += project_hashtags
                    
                    print(f"Generated Title: {youtube_title}")
                else:
                    print("Script file not found, skipping metadata generation.")
            except Exception as e:
                print(f"Error generating metadata: {e}")

            batch_processor.update_video_status(
                videos_json_path,
                video_item['index'],
                'generated',
                output_path=result['output_path'],
                youtube_title=youtube_title,
                youtube_description=youtube_description,
                youtube_tags=youtube_tags
            )
        else:
            batch_processor.update_video_status(
                videos_json_path,
                video_item['index'],
                'error',
                error_message=result.get('error')
            )

if __name__ == "__main__":
    main()
