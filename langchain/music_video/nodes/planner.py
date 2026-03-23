"""
planner.py — Planner Node

Reads the music database, calls Gemini to generate an idea (theme, prompts, metadata),
generates a cover image, and selects music tracks to fill the target duration.

On retry (retry_count > 0), the previous review_feedback is used to avoid
repeating the same creative direction.
"""

import json
import logging
import os

from langchain.music_video.state import VideoGenerationState
from langchain.music_video.tools.db_tools import (
    tool_get_music_inventory,
    tool_generate_idea,
    tool_generate_cover_image,
    tool_select_music,
)

logger = logging.getLogger(__name__)


def planner_node(state: VideoGenerationState) -> dict:
    """
    LangGraph node: Plan the video — idea generation, cover image, music selection.

    Input state keys used:
        mood, genre, duration_hours, enable_veo, dev_mode,
        retry_count, review_feedback, output_dir, assets_dir

    Output state updates:
        idea, selected_tracks, cover_image_path, error_message
    """
    logger.info("=" * 60)
    logger.info("🎯 PLANNER NODE — Starting")
    logger.info("=" * 60)

    retry_count = state.get("retry_count", 0)
    review_feedback = state.get("review_feedback")
    dev_mode = state.get("dev_mode", False)
    enable_veo = state.get("enable_veo", False)
    assets_dir = state["assets_dir"]

    # Ensure assets directory exists
    os.makedirs(assets_dir, exist_ok=True)

    # Define file paths
    idea_file = os.path.join(assets_dir, "idea.json")
    cover_image = os.path.join(assets_dir, "cover.png")
    selected_tracks_file = os.path.join(assets_dir, "selected_tracks.json")

    # On retry, clean previous artifacts to force regeneration
    if retry_count > 0:
        logger.info(f"🔄 Retry #{retry_count} — Cleaning previous artifacts")
        logger.info(f"   Previous feedback: {review_feedback}")
        for f in [idea_file, cover_image, selected_tracks_file]:
            if os.path.exists(f):
                os.remove(f)

    try:
        # Step 1: Get music inventory from SQLite
        inventory = tool_get_music_inventory()

        # Step 2: Generate idea via Gemini
        # Build avoidance list from user input + retry feedback
        avoid_genres = []
        if state.get("genre"):
            # If user specified a genre, we don't avoid it — we prefer it.
            # The avoid list is for retry scenarios.
            pass

        if retry_count > 0 and state.get("idea"):
            # Avoid the genre from the failed attempt
            failed_genre = state["idea"].get("genre")
            if failed_genre:
                avoid_genres.append(failed_genre)

        idea = tool_generate_idea(
            inventory,
            avoid_genres=avoid_genres if avoid_genres else None,
            dev_mode=dev_mode,
            review_feedback=review_feedback,
        )

        # If user specified mood/genre, override the LLM's choice
        if state.get("mood"):
            idea["mood"] = state["mood"]
        if state.get("genre"):
            idea["genre"] = state["genre"]

        # Save idea to file (needed by downstream tools that read from file)
        idea["cover_image_path"] = os.path.abspath(cover_image)
        with open(idea_file, "w") as f:
            json.dump(idea, f, indent=4)
        logger.info(f"Idea saved to {idea_file}")

        # Step 3: Generate cover image (skip if Veo will generate it)
        if not enable_veo:
            tool_generate_cover_image(idea, cover_image, dev_mode=dev_mode)

        # Step 4: Select music tracks
        duration_hours = state.get("duration_hours", 1)
        tracks_data = tool_select_music(idea_file, selected_tracks_file, duration_hours)

        logger.info("✅ PLANNER NODE — Complete")

        return {
            "idea": idea,
            "selected_tracks": tracks_data.get("tracks", []),
            "cover_image_path": os.path.abspath(cover_image),
            "error_message": None,
        }

    except Exception as e:
        logger.error(f"❌ PLANNER NODE — Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error_message": f"Planner failed: {e}",
        }
