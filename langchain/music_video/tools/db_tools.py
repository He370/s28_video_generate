"""
db_tools.py — Database & Idea Generation Tool Wrappers

Thin wrappers around existing functions from:
- projects.music_video.idea_generator
- projects.music_video.music_selector

These wrappers adapt the file-based I/O to work with the LangGraph state.
Original function signatures are preserved (read-only import).
"""

import json
import logging
import os
import sys

# Ensure the project root is on sys.path for imports
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from projects.music_video.idea_generator import get_music_inventory, generate_idea
from projects.music_video.music_selector import select_music

logger = logging.getLogger(__name__)


def tool_get_music_inventory():
    """
    Query the music database for available genre/mood combinations.
    Returns a list of dicts with 'genre', 'mood', and 'count' keys.
    """
    try:
        inventory = get_music_inventory()
        if not inventory:
            raise RuntimeError("Music inventory is empty. No tracks found in the database.")
        logger.info(f"Retrieved {len(inventory)} genre/mood combinations from DB")
        return inventory
    except Exception as e:
        logger.error(f"Failed to get music inventory: {e}")
        raise


def tool_generate_idea(
    inventory,
    existing_titles=None,
    avoid_genres=None,
    dev_mode=False,
    review_feedback=None,
):
    """
    Use Gemini to generate a video idea (theme, prompts, metadata).

    If review_feedback is provided (retry scenario), it can be used to
    guide the LLM toward a different creative direction.

    Returns the idea dict or None.
    """
    try:
        # On retry, we append the review feedback as additional avoidance context
        # by extending avoid_genres or existing_titles based on the feedback.
        # The generate_idea function handles avoid_genres natively.
        if review_feedback and avoid_genres is None:
            avoid_genres = []

        idea = generate_idea(
            inventory,
            existing_titles=existing_titles,
            avoid_genres=avoid_genres,
            dev_mode=dev_mode,
        )

        if idea is None:
            raise RuntimeError("Gemini failed to generate an idea")

        logger.info(f"Generated idea: {idea.get('title', 'Untitled')}")
        return idea
    except Exception as e:
        logger.error(f"Failed to generate idea: {e}")
        raise


def tool_generate_cover_image(idea, cover_image_path, dev_mode=False):
    """
    Generate a cover image using Imagen 4 based on the idea's image_prompt.
    Writes the image to cover_image_path.
    """
    try:
        image_prompt = idea.get("image_prompt")
        if not image_prompt:
            raise RuntimeError("No image_prompt found in idea")

        if os.path.exists(cover_image_path):
            logger.info(f"Cover image already exists at {cover_image_path}, reusing.")
            return cover_image_path

        from video_generation_tool.gemini_client import GeminiClient
        from video_generation_tool.constants import GEMINI_IMAGE_MODEL_IMAGEN4

        client = GeminiClient(mode="dev" if dev_mode else "prod")
        client.generate_image(
            prompt=image_prompt,
            output_path=cover_image_path,
            model=GEMINI_IMAGE_MODEL_IMAGEN4,
        )
        logger.info(f"Cover image generated at {cover_image_path}")
        return cover_image_path
    except Exception as e:
        logger.error(f"Failed to generate cover image: {e}")
        raise


def tool_select_music(idea_file, selected_tracks_file, duration_hours=1):
    """
    Select music tracks from the database based on the idea.
    Writes selected_tracks.json and returns the data dict.
    """
    try:
        select_music(idea_file, selected_tracks_file, duration_hours=duration_hours)

        if not os.path.exists(selected_tracks_file):
            raise RuntimeError("Music selection produced no output file")

        with open(selected_tracks_file, "r") as f:
            data = json.load(f)

        logger.info(f"Selected {len(data.get('tracks', []))} tracks")
        return data
    except Exception as e:
        logger.error(f"Failed to select music: {e}")
        raise
