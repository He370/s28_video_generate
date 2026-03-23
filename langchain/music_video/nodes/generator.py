"""
generator.py — Generator Node

Executes the actual video/audio rendering pipeline by calling existing tools:
1. Video Loop (static image or Veo)
2. Seamless Loop (Cut-Swap-Fade)
3. Title Overlay
4. Thumbnail
5. Audio Assembly
6. Final Video Assembly
"""

import logging
import os

from langchain.music_video.state import VideoGenerationState
from langchain.music_video.tools.media_tools import (
    tool_generate_video_loop,
    tool_create_seamless_loop,
    tool_add_title_overlay,
    tool_generate_thumbnail,
    tool_assemble_audio,
    tool_assemble_final_video,
)

logger = logging.getLogger(__name__)


def generator_node(state: VideoGenerationState) -> dict:
    """
    LangGraph node: Execute the full media generation pipeline.

    Input state keys used:
        idea, selected_tracks, cover_image_path, enable_veo, dev_mode,
        duration_hours, output_dir, assets_dir

    Output state updates:
        video_loop_path, seamless_loop_path, video_with_title_path,
        thumbnail_path, final_audio_path, final_video_path, error_message
    """
    logger.info("=" * 60)
    logger.info("🎬 GENERATOR NODE — Starting")
    logger.info("=" * 60)

    # If planner had an error, propagate it
    if state.get("error_message"):
        logger.error(f"Skipping generator due to previous error: {state['error_message']}")
        return {}

    dev_mode = state.get("dev_mode", False)
    enable_veo = state.get("enable_veo", False)
    duration_hours = state.get("duration_hours", 1)
    assets_dir = state["assets_dir"]
    output_dir = state["output_dir"]

    # File paths
    idea_file = os.path.join(assets_dir, "idea.json")
    cover_image = state.get("cover_image_path", os.path.join(assets_dir, "cover.png"))
    video_loop_file = os.path.join(assets_dir, "visuals_loop.mp4")
    seamless_loop_file = os.path.join(assets_dir, "visuals_loop_seamless.mp4")
    video_with_title_file = os.path.join(assets_dir, "visuals_loop_with_title.mp4")
    thumbnail_file = os.path.join(assets_dir, "thumbnail.jpg")
    selected_tracks_file = os.path.join(assets_dir, "selected_tracks.json")
    final_audio_file = os.path.join(assets_dir, "final_audio.mp3")
    final_video_file = os.path.join(output_dir, "final_video.mp4")

    updates = {}

    try:
        # ── Step 1: Video Loop ──
        logger.info("Step 1/6: Generating video loop...")
        if not os.path.exists(video_loop_file):
            tool_generate_video_loop(idea_file, video_loop_file, dev_mode=dev_mode, use_veo=enable_veo)
        else:
            logger.info("  Video loop already exists, skipping.")
        updates["video_loop_path"] = video_loop_file

        # ── Step 2: Seamless Loop ──
        logger.info("Step 2/6: Creating seamless loop...")
        if not os.path.exists(seamless_loop_file):
            actual_seamless = tool_create_seamless_loop(video_loop_file, seamless_loop_file)
        else:
            actual_seamless = seamless_loop_file
            logger.info("  Seamless loop already exists, skipping.")
        updates["seamless_loop_path"] = actual_seamless

        # ── Step 3: Title Overlay ──
        logger.info("Step 3/6: Adding title overlay...")
        if not os.path.exists(video_with_title_file):
            title_result = tool_add_title_overlay(idea_file, actual_seamless, video_with_title_file)
        else:
            title_result = video_with_title_file
            logger.info("  Title overlay already exists, skipping.")
        updates["video_with_title_path"] = title_result

        # ── Step 4: Thumbnail ──
        logger.info("Step 4/6: Generating thumbnail...")
        if not os.path.exists(thumbnail_file):
            thumb_result = tool_generate_thumbnail(idea_file, cover_image, thumbnail_file)
        else:
            thumb_result = thumbnail_file
            logger.info("  Thumbnail already exists, skipping.")
        updates["thumbnail_path"] = thumb_result

        # ── Step 5: Audio Assembly ──
        logger.info("Step 5/6: Assembling audio...")
        if not os.path.exists(final_audio_file):
            tool_assemble_audio(selected_tracks_file, final_audio_file)
        else:
            logger.info("  Audio already assembled, skipping.")
        updates["final_audio_path"] = final_audio_file

        # ── Step 6: Final Video Assembly ──
        logger.info("Step 6/6: Assembling final video...")
        if not os.path.exists(final_video_file):
            intro_video = title_result if title_result and os.path.exists(title_result) else None
            tool_assemble_final_video(
                final_audio_file,
                actual_seamless,
                final_video_file,
                duration_hours=duration_hours,
                intro_video=intro_video,
            )
        else:
            logger.info("  Final video already exists, skipping.")
        updates["final_video_path"] = final_video_file

        # Cleanup intermediate audio
        if os.path.exists(final_audio_file) and os.path.exists(final_video_file):
            os.remove(final_audio_file)
            logger.info(f"Cleaned up intermediate audio: {final_audio_file}")

        updates["error_message"] = None
        logger.info("✅ GENERATOR NODE — Complete")

    except Exception as e:
        logger.error(f"❌ GENERATOR NODE — Failed: {e}")
        import traceback
        traceback.print_exc()
        updates["error_message"] = f"Generator failed: {e}"

    return updates
