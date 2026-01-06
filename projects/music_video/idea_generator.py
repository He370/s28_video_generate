import os
import sys
import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
import datetime

# Add parent directory to path to import video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from video_generation_tool.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../music_lib/music.db'))
OUTPUT_FILE = 'idea.json'
COVER_IMAGE_FILE = 'cover_image.png'

def get_music_inventory() -> List[Dict[str, Any]]:
    """Query the music database for genre and mood counts, filtering by usage."""
    if not os.path.exists(DB_PATH):
        logging.error(f"Database not found at {DB_PATH}")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Find the minimum usage count in the entire DB
    cursor.execute("SELECT MIN(usage_count) FROM tracks")
    row = cursor.fetchone()
    min_usage = row[0] if row and row[0] is not None else 0
    
    target_usage = min_usage + 1
    logging.info(f"Filtering inventory: min_usage={min_usage}, target_usage_limit={target_usage}")
    
    # 2. Tracks with usage <= min_usage + 1
    # Fetch raw strings to process in Python
    query = """
        SELECT genre, mood
        FROM tracks 
        WHERE usage_count <= ?
    """
    cursor.execute(query, (target_usage,))
    rows = cursor.fetchall()
    conn.close()
    
    inventory_counts = {}

    for row in rows:
        # row[0] is genre string, row[1] is mood string
        raw_genres = row[0] if row[0] else "Unknown"
        raw_moods = row[1] if row[1] else "Unknown"
        
        genres = [g.strip() for g in raw_genres.split(',') if g.strip()]
        moods = [m.strip() for m in raw_moods.split(',') if m.strip()]
        
        if not genres: genres = ["Unknown"]
        if not moods: moods = ["Unknown"]
        
        for g in genres:
            for m in moods:
                key = (g, m)
                inventory_counts[key] = inventory_counts.get(key, 0) + 1
                
    inventory = []
    # Sort for consistent prompt output (by count desc, then alphabet)
    sorted_keys = sorted(inventory_counts.keys(), key=lambda k: (-inventory_counts[k], k[0], k[1]))
    
    for g, m in sorted_keys:
        # Skip "Unknown" genre - we want real genre names
        if g.lower() == 'unknown':
            continue
        inventory.append({
            "genre": g,
            "mood": m,
            "count": inventory_counts[(g, m)]
        })
        
    return inventory

def generate_idea(inventory: List[Dict[str, Any]], existing_titles: List[str] = [], avoid_genres: List[str] = [], dev_mode: bool = False) -> Optional[Dict]:
    """Call Gemini to generate a video idea based on inventory."""
    client = GeminiClient(mode="dev" if dev_mode else "prod")
    
    # Filter inventory to reduce noise (only combinations with >= 5 tracks)
    filtered_inventory = [item for item in inventory if item['count'] >= 5]
    
    # Fallback if too aggressive
    if not filtered_inventory and inventory:
        logging.warning("No inventory combinations with >= 5 tracks. Using top 5 available.")
        # inventory is already sorted by count desc
        filtered_inventory = inventory[:5]
    elif not filtered_inventory:
         logging.warning("Inventory is empty.")
         return None

    # Format inventory for the prompt
    inventory_str = "\n".join([f"- Genre: {item['genre']} | Mood: {item['mood']} ({item['count']} tracks)" for item in filtered_inventory])
    
    avoid_instruction = ""
    
    if avoid_genres:
        avoid_instruction += f"Prefer genres NOT in this list: {', '.join(avoid_genres)}. If necessary, you may reuse them, but prioritize unused genres from my inventory.\n"
    
    prompt = f"""
    I have the following music inventory (filtered for freshness and quantity):
    {inventory_str}
    
    Please generate a 'Relax & Focus' video theme for today.
    {avoid_instruction}
    
    Requirements:
    1. Theme must be specific (e.g., 'Rainy Coffee Shop Jazz' instead of just 'Relaxing Music').
    2. Select a target Genre and Mood from the inventory that fits the theme.
    3. Provide a YouTube Video Title.
    4. Provide a short YouTube Video Description.
    5. Provide a HIGHLY DETAILED, EXTREMELY INTRICATE Image Generation Prompt for a COZY LIVING ENVIRONMENT with rich details. PERFECTLY MATCHES the chosen Genre and Mood.
       - IMPORTANT: The scene must be a beautiful, static composition of a room or space.
       - BE VERY SPECIFIC about the lighting, textures, furniture, plant life, and small background details.
       - Include specific style keywords like "cinematic lighting, 8k, photorealistic".
    6. Provide a COMPLEMENTARY Video Generation Prompt (for Veo3) that works with the image prompt:
       - The video should show SUBTLE, NATURAL movements in the same scene (e.g., gentle rain falling, soft window light changing, plants swaying slightly)
       - CRITICAL: The prompt must be designed for SEAMLESS LOOPING - movements should be cyclical and natural
       - The video should maintain the same cozy atmosphere and composition as the image
       - Specify "8 seconds, 1080p, seamless loop, subtle motion, cinematic"
    7. Provide a list of 8-12 comma-separated YouTube Video Tags for search optimization (e.g. 'lofi hip hop, relaxation, study music').
    
    Output the result as a raw JSON object with keys: "theme", "genre", "mood", "title", "description", "tags", "image_prompt", "video_prompt".
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




def generate_idea_to_file(output_file: str, cover_image_file: str, existing_titles: List[str] = [], avoid_genres: List[str] = [], dev_mode: bool = False) -> Optional[Dict]:
    inventory = get_music_inventory()
    if not inventory:
        logging.error("No music found in inventory.")
        return None

    logging.info(f"Inventory: {inventory}")
    
    idea = generate_idea(inventory, existing_titles=existing_titles, avoid_genres=avoid_genres, dev_mode=dev_mode)
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

