import datetime
import json
import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path to import video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from video_generation_tool.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../music_lib/music.db'))
OUTPUT_FILE = 'idea.json'
COVER_IMAGE_FILE = 'cover_image.png'


def get_music_inventory() -> List[Dict[str, Any]]:
    """
    Query the music database for genre and mood counts with adaptive usage filtering.
    Iteratively increases the usage limit until combinations with >= 8 tracks are found.
    """
    if not os.path.exists(DB_PATH):
        logging.error(f"Database not found at {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get usage statistics to define search bounds
    cursor.execute("SELECT MIN(usage_count), MAX(usage_count) FROM tracks")
    stats = cursor.fetchone()
    min_usage = stats[0] if stats and stats[0] is not None else 0
    max_usage = stats[1] if stats and stats[1] is not None else 0

    target_usage = min_usage
    found_inventory = []

    logging.info(f"Inventory search: min_usage={min_usage}, max_usage={max_usage}")

    # Loop to find adequate inventory
    while target_usage <= max_usage + 1:
        # Query tracks with current target usage
        cursor.execute("SELECT genre, mood FROM tracks WHERE usage_count <= ?", (target_usage,))
        rows = cursor.fetchall()

        # Count combinations
        inventory_counts = {}
        for r_row in rows:
            raw_genres = r_row[0] if r_row[0] else "Unknown"
            raw_moods = r_row[1] if r_row[1] else "Unknown"

            genres = [g.strip() for g in raw_genres.split(',') if g.strip()]
            moods = [m.strip() for m in raw_moods.split(',') if m.strip()]

            if not genres:
                genres = ["Unknown"]
            if not moods:
                moods = ["Unknown"]

            for g in genres:
                for m in moods:
                    key = (g, m)
                    inventory_counts[key] = inventory_counts.get(key, 0) + 1

        # Flatten to list
        temp_inventory = []
        # Sort keys to ensure deterministic ordering before sorting by count
        sorted_keys = sorted(inventory_counts.keys())

        for g, m in sorted_keys:
            if g.lower() == 'unknown':
                continue
            count = inventory_counts[(g, m)]
            temp_inventory.append({"genre": g, "mood": m, "count": count})

        # Sort by count desc
        temp_inventory.sort(key=lambda x: x['count'], reverse=True)

        # Check for sufficient quantity (>= 8 tracks)
        # If we successfully find groups with >= 8 tracks, we preferentially return only those.
        valid_options = [x for x in temp_inventory if x['count'] >= 8]

        if valid_options:
            logging.info(f"Found {len(valid_options)} combinations with >= 8 tracks at usage_level={target_usage}")
            found_inventory = valid_options
            break

        # If we reached max usage (or went slightly past to be safe) and still nothing,
        # use whatever we have (sorted by count) as a fallback.
        if target_usage >= max_usage:
            logging.warning("Reached max usage without finding combinations >= 8 tracks. Using best available.")
            found_inventory = temp_inventory
            break

        # Increment and retry
        logging.info(f"No combos >= 8 tracks at usage={target_usage}. Increasing to {target_usage + 1}...")
        target_usage += 1

    conn.close()
    return found_inventory


def generate_idea(
    inventory: List[Dict[str, Any]],
    existing_titles: Optional[List[str]] = None,
    avoid_genres: Optional[List[str]] = None,
    dev_mode: bool = False
) -> Optional[Dict]:
    """Call Gemini to generate a video idea based on inventory."""
    if existing_titles is None:
        existing_titles = []
    if avoid_genres is None:
        avoid_genres = []

    client = GeminiClient(mode="dev" if dev_mode else "prod")

    # Select top 8 combinations to keep the prompt focused
    filtered_inventory = inventory[:8]

    if not filtered_inventory:
        logging.warning("Inventory is empty.")
        return None

    # Format inventory for the prompt
    inventory_str = "\n".join([f"- Genre: {item['genre']} | Mood: {item['mood']} ({item['count']} tracks)" for item in filtered_inventory])

    avoid_instruction = ""

    if avoid_genres:
        avoid_instruction += f"Prefer genres NOT in this list: {', '.join(avoid_genres)}. If necessary, you may reuse them, but prioritize unused genres from my inventory.\n"

    prompt = f"""
# Role
You are an expert AI YouTube Producer and Art Director. Your goal is to create a high-quality "Relax & Focus" video concept based on available music inventory.

# Input Data (Music Inventory)
{inventory_str}

# Task
Select the best matching Music Genre/Mood from the inventory and generate a cohesive video package.

# Visual Identity (STRICT)
The visual style must match the "Dark Biophilic Luxury" aesthetic:
1.  **Mood:** Melancholic yet cozy, "Blue Hour", moody, cinematic.
2.  **Colors:** Deep teal/cyan exterior tones vs. Warm amber/orange interior lights.
3.  **Architecture:** Modern minimalist, concrete/stone, floor-to-ceiling glass, views of dramatic nature (ocean, rain, cliffs).

# Output Requirements (JSON Keys)

1.  **"theme"**: A specific, evocative setting (e.g., "Stormy Cliffside Reading Nook", "Tokyo High-Rise Rain").
2.  **"genre"**: Selected from inventory. {avoid_instruction}
3.  **"mood"**: Selected from inventory.
4.  **"title"**: A high-CTR YouTube title (include emotion keywords, e.g., "Deep Focus", "Stress Relief").
5.  **"description"**: A short, engaging 2-sentence description.
6.  **"tags"**: 10-15 comma-separated high-volume keywords for SEO.

7.  **"image_prompt"**: (For Imagen 4)
        * Structure: [Architecture/Space Type] + [Contextual Interior Details] + [Environment/Weather] + [Lighting/Color] + [Material Details] + [Tech Specs].
        * **Crucial:** Focus on "Looking from inside out". Dark marble or wood textures. **Glass texture is key: specify "wet glass with condensation" or "rain-speckled window" rather than just "rain".**
        * Requirement for [Contextual Interior Details]: DO NOT produce empty rooms. You must creatively populate the space with 2-3 distinct items appropriate for the specific room type.
            ** If Study: Add items like "scattered blueprints," "vintage telescope," "stacked leather books," or "mechanical keyboard."**
            ** If Lounge: Add items like "plush velvet cushions," "crystal whiskey decanter," "cashmere throw blanket," or "low-profile coffee table."**
            ** If Bedroom: Add "rumpled silk sheets," "reading glasses on nightstand," or "soft slippers."**
        * Keywords to force: "Unreal Engine 5, 8k, volumetric fog, hyper-realistic, interior design, moody lighting".
        * Example: "A hyper-realistic wide shot of a luxury brutalist study room carved into a cliffside cave... Outside a massive glass wall, a stormy ocean crashes... **Glass pane is covered in detailed wet droplets.** Interior lit by a warm vintage desk lamp... Dark teal and amber color grading..."

8.  **"video_prompt"**: (For Veo 3 - Image-to-Video)
        * **Structure:** Describe motion in layers, but prioritize **GENTLENESS**:
            1.  **Background (Nature/The Dynamic Layer):** 
                - IF OCEAN: "Heavy ocean swells rolling and crashing continuously in slow motion."
                - IF FOREST/TREES: "Branches swaying GENTLY in a light breeze," "Fog drifting LAZILY and SLOWLY." (Avoid "blowing" or "fast").
            2.  **Foreground (Texture/The Static Layer):** - "Static condensation on glass," "Shimmering wet texture," "Subtle refraction." (NO sliding water, NO fast rain).
            3.  **Interior (Vibe):** "Candle flame flickering softly," "Steam rising slowly."
        * **Speed Control:** EXPLICITLY specify: "**Slow motion**, **time-stretched**, **dreamy atmosphere**, **60fps converted to 24fps**."
        * **Camera:** STRICTLY "Static Camera" or "Tripod Shot".
        * **Negative Constraint:** NEVER use "fast", "stormy wind", "active flow", "timelapse", "sliding down".
# Output Format
Return **ONLY** a raw JSON object. Do not use Markdown code blocks (```json).
{{
  "theme": "...",
  "genre": "...",
  "mood": "...",
  "title": "...",
  "description": "...",
  "tags": "...",
  "image_prompt": "...",
  "video_prompt": "..."
}}
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


def generate_idea_to_file(
    output_file: str,
    cover_image_file: str,
    existing_titles: Optional[List[str]] = None,
    avoid_genres: Optional[List[str]] = None,
    dev_mode: bool = False,
    skip_image_generation: bool = False
) -> Optional[Dict]:
    if existing_titles is None:
        existing_titles = []
    if avoid_genres is None:
        avoid_genres = []

    inventory = get_music_inventory()
    if not inventory:
        logging.error("No music found in inventory.")
        return None

    logging.info(f"Inventory (top matches): {inventory[:5]}")

    idea = generate_idea(inventory, existing_titles=existing_titles, avoid_genres=avoid_genres, dev_mode=dev_mode)
    if idea:
        logging.info(f"Generated Idea: {idea['title']}")

        # Determine image model - prioritizing the advanced image model for quality covers
        from video_generation_tool.constants import GEMINI_IMAGE_MODEL_IMAGEN4

        # Generate Cover Image
        image_prompt = idea.get('image_prompt')

        if not skip_image_generation:
            if image_prompt:
                logging.info("Generating cover image...")
                client = GeminiClient(mode="dev" if dev_mode else "prod")
                try:
                    client.generate_image(
                        prompt=image_prompt,
                        output_path=cover_image_file,
                        model=GEMINI_IMAGE_MODEL_IMAGEN4
                    )
                    idea['cover_image_path'] = os.path.abspath(cover_image_file)
                except Exception as e:
                    logging.error(f"Error generating cover image: {e}")
        else:
            logging.info("Skipping cover image generation (will be generated during video creation).")
            # We still set the path where it WILL be, so downstream tools know where to look
            idea['cover_image_path'] = os.path.abspath(cover_image_file)

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

