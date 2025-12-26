import os
import sys
import sqlite3
import json
import logging
from typing import Dict, List, Optional
import datetime

# Add parent directory to path to import video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from video_generation_tool.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../music_lib/music.db'))
OUTPUT_FILE = 'idea.json'
COVER_IMAGE_FILE = 'cover_image.png'

def get_music_inventory() -> Dict[str, int]:
    """Query the music database for genre counts."""
    if not os.path.exists(DB_PATH):
        logging.error(f"Database not found at {DB_PATH}")
        return {}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT genre, COUNT(*) FROM tracks GROUP BY genre")
    rows = cursor.fetchall()
    conn.close()
    
    inventory = {row[0]: row[1] for row in rows}
    return inventory

def generate_idea(inventory: Dict[str, int], existing_titles: List[str] = [], dev_mode: bool = False) -> Optional[Dict]:
    """Call Gemini to generate a video idea based on inventory."""
    client = GeminiClient(mode="dev" if dev_mode else "prod")
    
    inventory_str = ", ".join([f"{k}: {v} tracks" for k, v in inventory.items()])
    
    avoid_instruction = ""
    if existing_titles:
        avoid_instruction = f"Avoid the following themes/titles as they have already been used: {', '.join(existing_titles)}."
    
    prompt = f"""
    I have the following music inventory in my database: [{inventory_str}].
    
    Please generate a 'Relax & Focus' video theme for today.
    {avoid_instruction}
    
    Requirements:
    1. Theme must be specific (e.g., 'Rainy Coffee Shop Jazz' instead of just 'Relaxing Music').
    2. Specify the main Genre from my inventory to use.
    3. Specify a BPM range (e.g., 60-90) suitable for the theme.
    4. Provide a YouTube Video Title.
    5. Provide a short YouTube Video Description.
    6. Provide a HIGHLY DETAILED, EXTREMELY INTRICATE, and AESTHETICALLY RICH Image Generation Prompt for the video cover. BE VERY SPECIFIC about the lighting, textures, and small background details. The scene must be a beautiful, static composition suitable for subtle animation loop. Describe distinct elements in foreground, midground, and background to ensure depth. Include specific style keywords like "cinematic lighting, 8k, photorealistic, unreal engine 5, ray tracing, sharp focus, intricate details, atmospheric, masterpiece".
    7. Provide a list of 15-20 comma-separated YouTube Video Tags for search optimization (e.g. 'lofi hip hop, relaxation, study music').
    
    Output the result as a raw JSON object with keys: "theme", "genre", "bpm_range", "title", "description", "tags", "image_prompt".
    Do not include markdown formatting like ```json ... ```.
    """
    
    logging.info("Calling Gemini for idea generation...")
    response_text = client.generate_text(prompt, response_mime_type="application/json")
    
    try:
        # Clean up potential markdown wrapping
        if response_text.strip().startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "")
            
        idea = json.loads(response_text)
        
        # Ensure tags is a list
        tags_raw = idea.get("tags", "")
        if isinstance(tags_raw, str):
            idea["tags"] = [t.strip() for t in tags_raw.split(',') if t.strip()]
        
        return idea
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response: {e}")
        logging.error(f"Response was: {response_text}")
        return None



def generate_idea_to_file(output_file: str, cover_image_file: str, existing_titles: List[str] = [], dev_mode: bool = False) -> Optional[Dict]:
    inventory = get_music_inventory()
    if not inventory:
        logging.error("No music found in inventory.")
        return None

    logging.info(f"Inventory: {inventory}")
    
    idea = generate_idea(inventory, existing_titles=existing_titles, dev_mode=dev_mode)
    if idea:
        logging.info(f"Generated Idea: {idea['title']}")
        
        # Determine image model - prioritizing the advanced image model for quality covers
        from video_generation_tool.constants import GEMINI_IMAGE_ADVANCED_MODEL
        
        # Generate Cover Image
        image_prompt = idea.get('image_prompt')
        if image_prompt:
            logging.info("Generating cover image...")
            client = GeminiClient(mode="dev" if dev_mode else "prod")
            try:
                client.generate_image(
                    prompt=image_prompt, 
                    output_path=cover_image_file,
                    model=GEMINI_IMAGE_ADVANCED_MODEL
                )
                idea['cover_image_path'] = os.path.abspath(cover_image_file)
            except Exception as e:
                logging.error(f"Error generating cover image: {e}")
        
        # Save idea to file
        with open(output_file, 'w') as f:
            json.dump(idea, f, indent=4)
        logging.info(f"Idea saved to {output_file}")
        
        return idea
                
    else:
        logging.error("Failed to generate idea.")
        return None

if __name__ == "__main__":
    generate_idea_to_file('idea.json', 'cover_image.png')

