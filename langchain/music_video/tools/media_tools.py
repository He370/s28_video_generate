"""
media_tools.py — Media Generation & Assembly Tool Wrappers

Thin wrappers around existing functions from:
- projects.music_video.video_looper
- projects.music_video.seamless_loop_processor
- projects.music_video.title_overlay
- projects.music_video.thumbnail_generator
- projects.music_video.audio_assembler
- projects.music_video.final_assembler

Original function signatures are preserved (read-only import).
"""

import logging
import os
import sys

# Ensure the project root is on sys.path for imports
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from projects.music_video.video_looper import generate_video_loop
from projects.music_video.seamless_loop_processor import create_seamless_loop
from projects.music_video.title_overlay import add_title_overlay
from projects.music_video.thumbnail_generator import generate_thumbnail
from projects.music_video.audio_assembler import assemble_audio
from projects.music_video.final_assembler import assemble_final_video

logger = logging.getLogger(__name__)


def tool_generate_video_loop(idea_file, output_video_file, dev_mode=False, use_veo=False):
    """
    Generate an 8-second video loop (static image or Veo-based).
    """
    try:
        generate_video_loop(idea_file, output_video_file, dev_mode=dev_mode, use_veo=use_veo)

        if not os.path.exists(output_video_file):
            raise RuntimeError("Video loop generation produced no output file")

        logger.info(f"Video loop generated: {output_video_file}")
        return output_video_file
    except Exception as e:
        logger.error(f"Failed to generate video loop: {e}")
        raise


def tool_create_seamless_loop(input_video, output_video):
    """
    Apply the Cut-Swap-Fade technique to create a seamless loop.
    """
    try:
        success = create_seamless_loop(input_video, output_video)
        if not success or not os.path.exists(output_video):
            logger.warning("Seamless loop creation failed, falling back to original video")
            return input_video  # Graceful fallback

        logger.info(f"Seamless loop created: {output_video}")
        return output_video
    except Exception as e:
        logger.warning(f"Seamless loop failed (non-fatal): {e}, using original video")
        return input_video


def tool_add_title_overlay(idea_file, input_video, output_video):
    """
    Add a Vogue-style title overlay to the video loop (for intro segment).
    """
    try:
        success = add_title_overlay(idea_file, input_video, output_video)
        if not success or not os.path.exists(output_video):
            logger.warning("Title overlay failed, intro will use plain loop")
            return None

        logger.info(f"Title overlay added: {output_video}")
        return output_video
    except Exception as e:
        logger.warning(f"Title overlay failed (non-fatal): {e}")
        return None


def tool_generate_thumbnail(idea_file, cover_image, output_path):
    """
    Generate a YouTube thumbnail using the Vogue magazine style.
    """
    try:
        generate_thumbnail(idea_file, cover_image, output_path)

        if not os.path.exists(output_path):
            logger.warning("Thumbnail generation failed")
            return None

        logger.info(f"Thumbnail generated: {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"Thumbnail generation failed (non-fatal): {e}")
        return None


def tool_assemble_audio(tracks_file, output_audio):
    """
    Assemble selected music tracks into a single audio file with looping.
    """
    try:
        assemble_audio(tracks_file, output_audio)

        if not os.path.exists(output_audio):
            raise RuntimeError("Audio assembly produced no output file")

        logger.info(f"Audio assembled: {output_audio}")
        return output_audio
    except Exception as e:
        logger.error(f"Failed to assemble audio: {e}")
        raise


def tool_assemble_final_video(audio_file, video_loop, output_video, duration_hours=1, intro_video=None):
    """
    Combine video loop and audio into the final video.
    """
    try:
        assemble_final_video(
            audio_file,
            video_loop,
            output_video,
            duration_hours=duration_hours,
            intro_video=intro_video,
        )

        if not os.path.exists(output_video):
            raise RuntimeError("Final video assembly produced no output file")

        logger.info(f"Final video assembled: {output_video}")
        return output_video
    except Exception as e:
        logger.error(f"Failed to assemble final video: {e}")
        raise
