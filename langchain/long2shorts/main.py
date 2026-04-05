"""
main.py — CLI Entrypoint for the LangGraph Long2Shorts Agent

Converts a long-form video's assets into a 30-40 second vertical YouTube Short.

Usage:
    python -m langchain.long2shorts.main --video-dir <path> --style <style>

Example:
    python -m langchain.long2shorts.main \
        --video-dir projects/horror_story/output/video_84 \
        --style "Horror"
"""

import argparse
import datetime
import json
import logging
import os
import random
import sys

# Ensure the project root is on sys.path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, "video_generation_tool", ".env"))

from langchain.long2shorts.graph import build_graph
from langchain.long2shorts.state import VideoState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_segments(video_dir: str) -> list:
    """
    Load segments.json from the video directory's assets folder.

    Args:
        video_dir: Path to the video_XX directory

    Returns:
        List of segment dicts
    """
    segments_path = os.path.join(video_dir, "assets", "segments.json")

    if not os.path.exists(segments_path):
        raise FileNotFoundError(f"segments.json not found at: {segments_path}")

    with open(segments_path, "r") as f:
        segments = json.load(f)

    logger.info(f"Loaded {len(segments)} segments from {segments_path}")
    return segments


def main():
    parser = argparse.ArgumentParser(
        description="🎬 Long2Shorts Agent — Convert long-form videos to YouTube Shorts"
    )
    parser.add_argument(
        "--video-dir", type=str, required=True,
        help="Path to the video_XX directory (e.g. projects/horror_story/output/video_84)"
    )
    parser.add_argument(
        "--style", type=str, default="Horror",
        help="Style category (e.g. 'Horror', 'Fairy Tale', 'History')"
    )
    parser.add_argument(
        "--output-dir", type=str, default="",
        help="Custom output directory (default: auto-generated under langchain/long2shorts/output/)"
    )
    parser.add_argument(
        "--dev", action="store_true",
        help="Run in dev mode (uses mock APIs)"
    )

    args = parser.parse_args()

    # ── Resolve paths ──
    video_dir = os.path.abspath(args.video_dir)
    if not os.path.isdir(video_dir):
        logger.error(f"Video directory not found: {video_dir}")
        sys.exit(1)

    # ── Determine output directory ──
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
    else:
        base_output = os.path.join(os.path.dirname(__file__), "output")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(base_output, f"run_{timestamp}")

    assets_dir = os.path.join(output_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # ── Load segments ──
    segments = load_segments(video_dir)

    # ── Resolve BGM directory ──
    # video_dir is like: projects/horror_story/output/video_84
    # BGM dir is like:   projects/horror_story/BGM
    project_dir = os.path.abspath(os.path.join(video_dir, "..", ".."))
    bgm_dir = os.path.join(project_dir, "BGM")
    if os.path.isdir(bgm_dir):
        logger.info(f"  BGM Dir:   {bgm_dir}")
    else:
        bgm_dir = None
        logger.info(f"  BGM Dir:   (not found)")

    logger.info("=" * 70)
    logger.info("🎬 Long2Shorts Agent — LangGraph Pipeline")
    logger.info("=" * 70)
    logger.info(f"  Source:    {video_dir}")
    logger.info(f"  Style:     {args.style}")
    logger.info(f"  Segments:  {len(segments)}")
    logger.info(f"  BGM:       {bgm_dir or '(none)'}")
    logger.info(f"  Output:    {output_dir}")
    logger.info("=" * 70)

    # ── Build initial state ──
    initial_state: VideoState = {
        "input_video_dir": video_dir,
        "input_segments": segments,
        "style_category": args.style,
        "dev_mode": args.dev,
        "short_script": None,
        "veo_assets": None,
        "audio_assets": None,
        "final_video_path": None,
        "output_dir": output_dir,
        "assets_dir": assets_dir,
        "error_message": None,
        "bgm_dir": bgm_dir,
    }

    # ── Build and run the graph ──
    graph = build_graph()

    logger.info("Starting LangGraph execution...")
    final_state = graph.invoke(initial_state)

    # ── Report results ──
    logger.info("")
    logger.info("=" * 70)

    if final_state.get("final_video_path") and os.path.exists(final_state["final_video_path"]):
        logger.info("🎉 SUCCESS — YouTube Short generated!")
        logger.info(f"  Final Video: {final_state['final_video_path']}")

        if final_state.get("short_script"):
            script = final_state["short_script"]
            logger.info(f"  Duration:    {script.get('total_duration', 'N/A')}s")
            logger.info(f"  Scenes:      {len(script.get('timeline', []))}")
    else:
        logger.error("💀 FAILED — Video generation did not complete.")
        logger.error(f"  Error: {final_state.get('error_message', 'Unknown error')}")
        sys.exit(1)

    logger.info("=" * 70)


if __name__ == "__main__":
    main()
