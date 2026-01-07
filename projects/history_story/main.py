import argparse
import os
import sys
import json
import random
import glob
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
    Generate a history story video based on a video item configuration.
    """
    video_index = video_item.get('index')
    topic = video_item.get('topic', 'Unknown Topic')
    story_type = video_item.get('type', 'mystery') # 'what_if' or 'mystery'
    debug_scene_limit = video_item.get('debug_scene_limit', None)
    image_style = video_item.get('image_style', 'cinematic, photorealistic')
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
        # Note: audio_gen is passed as parameter, respecting the language/voice settings
        # from the main() initialization. Do not create a new instance here.

        # 1. Generate or Load Script
        script_path = os.path.join(assets_dir, "script.txt")
        
        if os.path.exists(script_path):
            print(f"Loading existing script from {script_path}")
            with open(script_path, "r") as f:
                script = f.read()
        else:
            print("Generating story script...")
            
            if story_type == 'what_if':
                context = f"""
                Create a compelling "What If" scenario video script about: "{topic}".
                Explore the potential consequences, changes in history, and the state of the world if this event had happened differently.
                The tone should be speculative, engaging, and thought-provoking.
                Structure it as a narrative journey.
                """
                target_word_limit = 600
            elif story_type == 'historical_personage':
                context = f"""
                Create a detailed biographical video script about: "{topic}".
                Cover their early life, rise to prominence, key achievements or battles, and their lasting legacy.
                The tone should be epic, dramatic, and respectful.
                Structure it as a comprehensive life story.
                """
                target_word_limit = 2000
            else: # mystery
                context = f"""
                Create a documentary-style video script revealing the secrets of: "{topic}".
                Dive deep into the history, the theories, and the archaeological findings.
                The tone should be mysterious, educational, and awe-inspiring.
                Structure it as a journey of discovery.
                """
                target_word_limit = 600
            
            script = script_gen.generate_script(
                context=context,
                language=language,
                category="History Mystery",
                word_limit=target_word_limit # Adapted based on story type
            )
            
            if not script:
                return {"success": False, "error": "Failed to generate script"}
            
            # Save script
            with open(script_path, "w") as f:
                f.write(script)
            print(f"Script saved to {script_path}")
        
        # 2. Process Script into Scenes
        segments_log_path = os.path.join(assets_dir, "segments.json")
        
        if os.path.exists(segments_log_path):
            print(f"Loading existing segments from {segments_log_path}")
            with open(segments_log_path, "r") as f:
                segments = json.load(f)
                
            if debug_scene_limit and len(segments) > debug_scene_limit:
                segments = segments[:debug_scene_limit]
        else:
            print("Processing script into scenes...")
            
            # Define story-specific split prompt
            split_prompt = f"""
            I have a video script about a historical mystery or what-if scenario. Please split it into logical scenes for video narration.
            Each scene should be a coherent segment suitable for a single visual representation.
            
            Script:
            {script}
            
            Output strictly in JSON format as a list of objects:
            [
                {{
                    "text": "Paragraph text...",
                    "visual_idea": "A brief description of what should be seen (e.g., 'Ruins of Atlantis under water', 'Roman soldiers in modern New York')"
                }},
                ...
            ]
            """

            # Define image generator callback
            def story_image_prompt_generator(scene_text: str, index: int, metadata: dict) -> str:
                is_title = (index == 0)
                visual_idea = metadata.get("visual_idea", "")
                
                # Combine text context and visual idea
                prompt_context = f"Scene description: {visual_idea}. Context from narration: {scene_text}"
                
                if image_style:
                    styled_text = f"[Style: {image_style}] {prompt_context}"
                else:
                    styled_text = prompt_context
                
                if is_title:
                    if story_type == 'historical_personage':
                        title_prompt_request = f"""
                        Create a prompt for a modern poster style image for a biography about "{topic}".
                        The image should feature the historical figure prominently, looking epic and legendary.
                        The composition should be vertical or suitable for a poster with a modern design and attractive art style.
                        
                        Style: {image_style}
                        """
                        image_prompt = client.generate_image_prompt(title_prompt_request)
                        text_instruction = f"\n\nIMPORTANT: Create a poster style image. Include the name '{topic}' in a large, epic font suitable for a poster."
                        image_prompt += text_instruction
                    else:
                        title_prompt_request = f"""
                        Create a prompt for a stunning title card image for a video about "{topic}".
                        The image should be visually arresting and summarize the theme ({story_type}).
                        
                        Style: {image_style}
                        """
                        image_prompt = client.generate_image_prompt(title_prompt_request)
                        
                        # Add text instruction for title
                        text_instruction = f"\n\nIMPORTANT: Create a cinematic title card. Include the text '{topic}' centered. Font should be consistent with the style."
                        image_prompt += text_instruction
                else:
                    image_prompt = client.generate_image_prompt(styled_text)
                
                return image_prompt

            scenes = script_gen.process_script(
                script_text=script,
                split_prompt=split_prompt,
                image_prompt_generator_func=story_image_prompt_generator,
                debug_scene_limit=debug_scene_limit
            )
            
            if not scenes:
                return {"success": False, "error": "Failed to process script"}
            
            # 3. Initialize Segments and Save
            segments = []
            for i, scene in enumerate(scenes):
                img_path = os.path.join(assets_dir, f"scene_{i}.png")
                audio_path = os.path.join(assets_dir, f"scene_{i}.mp3")
                
                segment_data = {
                    "image": img_path,
                    "audio": audio_path,
                    "text": scene.get("text", ""),
                    "image_prompt": scene.get("image_prompt", ""),
                    "ken_burns": (i > 0) # Enable Ken Burns for non-title scenes
                }
                segments.append(segment_data)
            
            with open(segments_log_path, "w") as f:
                json.dump(segments, f, indent=4)
            print(f"Initial segments logged to {segments_log_path}")

        # 4. Generate Assets (Image and Audio)
        print("Generating assets for segments...")
        import time
        MAX_RETRIES = 3
        
        for i, segment in enumerate(segments):
            print(f"Processing Scene {i+1}/{len(segments)}...")
            
            img_path = segment["image"]
            audio_path = segment["audio"]
            image_prompt = segment["image_prompt"]
            scene_text = segment["text"]
            
            # Image
            if os.path.exists(img_path):
                print(f"  Image exists.")
            else:
                from video_generation_tool.utils import generate_image_with_retry
                from video_generation_tool.constants import GEMINI_IMAGE_ADVANCED_MODEL
                
                # Use advanced model for title card (scene 0)
                model_to_use = GEMINI_IMAGE_ADVANCED_MODEL if i == 0 else None
                
                success = generate_image_with_retry(
                    client=client,
                    image_prompt=image_prompt,
                    output_path=img_path,
                    max_retries=MAX_RETRIES,
                    max_times_gen_new_prompt=1,
                    model=model_to_use
                )
                
                if not success:
                    print(f"  Failed to generate image for scene {i}.")
            
            # Audio
            if os.path.exists(audio_path):
                print(f"  Audio exists.")
            else:
                try:
                    audio_gen.generate_audio_sync(scene_text, audio_path)
                except Exception as e:
                     print(f"  Error generating audio: {e}")
        
        # 5. Create Video
        print("Creating video...")
        
        # Prepare BGM
        bgm_dir = os.path.join(os.path.dirname(__file__), "BGM")
        bgm_files = glob.glob(os.path.join(bgm_dir, "*.mp3"))
        if bgm_files:
            random.shuffle(bgm_files)
            print(f"Found {len(bgm_files)} BGM files. Using sequential playback.")
        else:
            print(f"No BGM files found in {bgm_dir}")
            
        video_filename = f"video_{video_index}.mp4"
        video_path = os.path.join(video_dir, video_filename)
        video_maker = VideoMaker(output_file=video_path)
        video_maker.create_video(segments, bgm_files=bgm_files, bgm_volume=0.15)
        print(f"Video created successfully: {video_path}")
        
        return {"success": True, "output_path": video_path}
        
    except Exception as e:
        error_msg = f"Error generating video: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

def main():
    parser = argparse.ArgumentParser(description="Generate history story videos.")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--mode", choices=["prod", "dev"], default="dev", help="Mode: 'prod' or 'dev'")
    args = parser.parse_args()

    # Setup paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    output_base_dir = os.path.join(project_dir, "output")
    ensure_dir(output_base_dir)
    
    print(f"{'='*60}")
    print(f"Batch Video Generation - History Story")
    print(f"Mode: {args.mode}")
    print(f"{'='*60}\n")
    
    # Load video queue
    videos = batch_processor.load_video_queue(videos_json_path)
    pending_videos = batch_processor.get_pending_videos(videos, args.count)
    
    if not pending_videos:
        print("No pending videos found. Run idea_generator.py first.")
        return
    
    # Initialize clients
    try:
        client = GeminiClient(mode=args.mode)
        script_gen = ScriptGenerator(client)
        script_gen = ScriptGenerator(client)
        audio_gen = AudioGenerator(mode=args.mode)
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
                        style=video_item.get('type')
                    )
                    
                    youtube_title = metadata.get("title", "")
                    youtube_description = metadata.get("description", "")
                    youtube_tags = metadata.get("tags", [])
                    
                    # Add project specific hashtags
                    project_hashtags = "\n\n#History #Mystery #Documentary #Story"
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
