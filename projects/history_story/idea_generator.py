import os
import sys
import json
import argparse
from typing import List, Dict, Optional

# Add the project root to sys.path to allow imports from video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool.gemini_client import GeminiClient
from video_generation_tool import batch_processor

def generate_ideas(client: GeminiClient, count: int, existing_topics: List[str], target_type: str = "all", language: str = "English") -> List[Dict]:
    """Generate video ideas using Gemini."""
    
    # Summarize existing topics to avoid duplication
    # If there are many topics, we might want to truncate or sample, but for now we list them.
    # We join them to save some token overhead compared to full JSON structure if it was complex.
    existing_summary = "; ".join(existing_topics)
    
    import random
    
    type_instruction = ""
    if target_type == "all":
        # Randomly pick one type for this batch to keep it focused, or let the model mix.
        # The user requested: "if type is not specified, take it a random type from what_if or mystery"
        target_type = random.choice(["what_if", "mystery"])
        print(f"Randomly selected type: {target_type}")

    if target_type == "what_if":
        type_instruction = 'Focus ONLY on "What If" scenarios (alternate history).'
    elif target_type == "mystery":
        type_instruction = 'Focus ONLY on Ancient Civilization Mysteries.'

    prompt = f"""
    Generate {count} unique and intriguing video ideas for a "History Story" channel.
    Language: {language}
    
    {type_instruction}
    
    Ensure the topics are diverse and catchy.
    
    Existing topics to AVOID (do not repeat these):
    {existing_summary}
    
    Output strictly in JSON format as a list of objects:
    [
        {{
            "topic": "The Topic Title",
            "type": "what_if" or "mystery",
            "description": "A brief description of the video concept."
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
    parser = argparse.ArgumentParser(description="Generate video ideas for History Story project.")
    parser.add_argument("--count", type=int, default=5, help="Number of ideas to generate")
    parser.add_argument("--mode", choices=["prod", "dev"], default="dev", help="Mode: 'prod' or 'dev'")
    parser.add_argument("--type", choices=["all", "what_if", "mystery"], default="all", help="Type of stories to generate")
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
            "image_style": "cinematic, photorealistic, historical documentary style",
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
