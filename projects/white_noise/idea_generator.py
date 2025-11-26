import os
import sys
import json
import argparse
from typing import List, Dict
import random

# Add the project root to sys.path to allow imports from video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool.gemini_client import GeminiClient
from video_generation_tool import batch_processor

def generate_ideas(client: GeminiClient, count: int, existing_topics: List[str]) -> List[Dict]:
    """Generate video ideas using Gemini."""
    
    existing_summary = "; ".join(existing_topics)
    
    prompt = f"""
    Generate {count} unique and relaxing/focus-oriented video ideas for a "White Noise" channel.
    
    Each idea should consist of a single, visually appealing scene and a corresponding soundscape.
    
    Examples:
    - "Cozy library with rain outside"
    - "Futuristic spaceship engine room"
    - "Forest stream with birds chirping"
    - "Crackling fireplace in a cabin"
    
    Existing topics to AVOID (do not repeat these):
    {existing_summary}
    
    Output strictly in JSON format as a list of objects:
    [
        {{
            "topic": "Short Title",
            "scene_description": "Detailed visual description of the scene for image generation.",
            "art_style": "The artistic style (e.g., 'photorealistic', 'lo-fi anime', 'oil painting').",
            "duration_minutes": 30
        }},
        ...
    ]
    """
    
    try:
        response = client.generate_text(prompt, response_mime_type="application/json")
        ideas = json.loads(response)
        return ideas
    except Exception as e:
        print(f"Error generating ideas: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Generate video ideas for White Noise project.")
    parser.add_argument("--count", type=int, default=5, help="Number of ideas to generate")
    parser.add_argument("--mode", choices=["prod", "dev"], default="dev", help="Mode: 'prod' or 'dev'")
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
    
    new_ideas = generate_ideas(client, args.count, existing_topics)
    
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
            "scene_description": idea["scene_description"],
            "art_style": idea["art_style"],
            "duration_minutes": idea.get("duration_minutes", 30),
            "status": "pending"
        }
        
        batch_processor.add_video_to_queue(videos_json_path, video_item)
        print(f"Added: {idea['topic']}")
        added_count += 1
        
    print(f"\nSuccessfully added {added_count} new video ideas to videos.json")

if __name__ == "__main__":
    main()
