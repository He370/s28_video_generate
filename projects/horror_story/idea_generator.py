import os
import sys
import json
import argparse
from typing import List, Dict, Optional
import random

# Add the project root to sys.path to allow imports from video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool.gemini_client import GeminiClient
from video_generation_tool import batch_processor

def generate_ideas(client: GeminiClient, count: int, existing_topics: List[str], target_type: str = "all", language: str = "English") -> List[Dict]:
    """Generate video ideas using Gemini."""
    
    existing_summary = "; ".join(existing_topics)
    
    type_instruction = ""
    if target_type == "all":
        target_type = random.choice(["rules_horror", "urban_legend"])
        print(f"Randomly selected type: {target_type}")

    if target_type == "rules_horror":
        type_instruction = 'Focus ONLY on "Rules Horror" stories (a list of creepy rules for a specific situation or location).'
    elif target_type == "urban_legend":
        type_instruction = 'Focus ONLY on "Urban Legends" (modern folklore, scary stories passed around).'

    prompt = f"""
    Generate {count} unique and terrifying video ideas for a "Horror Story" channel.
    Language: {language}
    
    {type_instruction}
    
    Ensure the topics are diverse, spine-chilling, and catchy.
    
    Existing topics to AVOID (do not repeat these):
    {existing_summary}
    
    Output strictly in JSON format as a list of objects:
    [
        {{
            "topic": "The Topic Title",
            "type": "{target_type}",
            "description": "A brief description of the horror concept."
        }},
        ...
    ]
    """
    
    try:
        response = client.generate_text(prompt, response_mime_type="application/json")
        ideas = json.loads(response)
        # Ensure type is set correctly in case the model missed it or we are in 'all' mode
        for idea in ideas:
            if 'type' not in idea or idea['type'] not in ["rules_horror", "urban_legend"]:
                 idea['type'] = target_type
        return ideas
    except Exception as e:
        print(f"Error generating ideas: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Generate video ideas for Horror Story project.")
    parser.add_argument("--count", type=int, default=5, help="Number of ideas to generate")
    parser.add_argument("--mode", choices=["prod", "dev"], default="dev", help="Mode: 'prod' or 'dev'")
    parser.add_argument("--type", choices=["all", "rules_horror", "urban_legend"], default="all", help="Type of stories to generate")
    parser.add_argument("--language", type=str, default="English", help="Language for the video ideas")
    args = parser.parse_args()
    
    # Setup paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    
    # Initialize client
    try:
        client = GeminiClient(mode=args.mode)
    except ValueError as e:
        print(f"Error initializing Gemini client: {e}")
        return

    # Load existing videos to get used topics
    existing_videos = batch_processor.load_video_queue(videos_json_path)
    existing_topics = [v.get("topic") for v in existing_videos if v.get("topic")]
    
    print(f"Generating {args.count} new video ideas...")
    print(f"Type: {args.type}")
    print(f"Language: {args.language}")
    
    new_ideas = generate_ideas(client, args.count, existing_topics, args.type, args.language)
    
    if not new_ideas:
        print("No ideas generated.")
        return
        
    print(f"Generated {len(new_ideas)} ideas.")
    
    # Add to queue
    added_count = 0
    for idea in new_ideas:
        # Create video item structure
        video_item = {
            "topic": idea["topic"],
            "type": idea["type"],
            "description": idea["description"],
            "language": args.language,
            "image_style": "dark, eerie, cinematic horror, photorealistic",
            # Default settings
            "events": 6, 
            "debug_scene_limit": None
        }
        
        batch_processor.add_video_to_queue(videos_json_path, video_item)
        print(f"Added: {idea['topic']} ({idea['type']})")
        added_count += 1
        
    print(f"\nSuccessfully added {added_count} new video ideas to videos.json")

if __name__ == "__main__":
    main()
