"""
main.py — CLI Entrypoint for the LangGraph Music Video Agent

Usage:
    python -m langchain.music_video.main [OPTIONS]

Options:
    --mood TEXT         Desired mood (e.g. "Relaxing"). Optional — LLM decides if omitted.
    --genre TEXT        Desired genre (e.g. "Jazz"). Optional — LLM decides if omitted.
    --hours INT         Video duration in hours (default: 1)
    --max-retries INT   Max retry attempts before giving up (default: 2)
    --enable-veo        Use Veo for video generation (default: static image loop)
    --dev               Development mode (dummy generation, skip API calls)
    --output-dir TEXT   Custom output directory (default: auto-generated)
"""

import argparse
import datetime
import logging
import os
import sys

# Ensure the project root is on sys.path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from langchain.music_video.graph import build_graph
from langchain.music_video.state import VideoGenerationState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="🎬 LangGraph Music Video Agent — Agentic video generation workflow"
    )
    parser.add_argument("--mood", type=str, default="", help="Desired mood (e.g. 'Relaxing')")
    parser.add_argument("--genre", type=str, default="", help="Desired genre (e.g. 'Jazz')")
    parser.add_argument("--hours", type=int, default=1, help="Video duration in hours")
    parser.add_argument("--max-retries", type=int, default=2, help="Max retry attempts")
    parser.add_argument("--enable-veo", action="store_true", help="Use Veo for video gen")
    parser.add_argument("--dev", action="store_true", help="Development mode")
    parser.add_argument("--output-dir", type=str, default="", help="Custom output directory")

    args = parser.parse_args()

    # ── Determine output directory ──
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Default: langchain/music_video/output/run_<timestamp>
        base_output = os.path.join(os.path.dirname(__file__), "output")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(base_output, f"run_{timestamp}")

    assets_dir = os.path.join(output_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    logger.info("=" * 70)
    logger.info("🎬 LangGraph Music Video Agent")
    logger.info("=" * 70)
    logger.info(f"  Mood:        {args.mood or '(auto)'}")
    logger.info(f"  Genre:       {args.genre or '(auto)'}")
    logger.info(f"  Duration:    {args.hours}h")
    logger.info(f"  Max Retries: {args.max_retries}")
    logger.info(f"  Veo:         {'enabled' if args.enable_veo else 'disabled'}")
    logger.info(f"  Dev Mode:    {'yes' if args.dev else 'no'}")
    logger.info(f"  Output:      {output_dir}")
    logger.info("=" * 70)

    # ── Build initial state ──
    initial_state: VideoGenerationState = {
        "mood": args.mood,
        "genre": args.genre,
        "duration_hours": args.hours,
        "enable_veo": args.enable_veo,
        "dev_mode": args.dev,
        "retry_count": 0,
        "max_retries": args.max_retries,
        "output_dir": output_dir,
        "assets_dir": assets_dir,
        "review_passed": False,
        "review_feedback": None,
        "error_message": None,
        "idea": None,
        "selected_tracks": None,
        "cover_image_path": None,
        "video_loop_path": None,
        "seamless_loop_path": None,
        "video_with_title_path": None,
        "thumbnail_path": None,
        "final_audio_path": None,
        "final_video_path": None,
    }

    # ── Build and run the graph ──
    graph = build_graph()

    logger.info("Starting LangGraph execution...")
    final_state = graph.invoke(initial_state)

    # ── Report results ──
    logger.info("")
    logger.info("=" * 70)

    if final_state.get("review_passed"):
        logger.info("🎉 SUCCESS — Video generation complete!")
        logger.info(f"  Final Video: {final_state.get('final_video_path', 'N/A')}")
        logger.info(f"  Thumbnail:   {final_state.get('thumbnail_path', 'N/A')}")
        if final_state.get("idea"):
            logger.info(f"  Title:       {final_state['idea'].get('title', 'N/A')}")
            logger.info(f"  Genre:       {final_state['idea'].get('genre', 'N/A')}")
            logger.info(f"  Mood:        {final_state['idea'].get('mood', 'N/A')}")
    else:
        logger.error("💀 FAILED — Video generation did not pass quality review.")
        logger.error(f"  Retries:     {final_state.get('retry_count', 0)}/{args.max_retries}")
        logger.error(f"  Last Error:  {final_state.get('error_message', 'N/A')}")
        logger.error(f"  Feedback:    {final_state.get('review_feedback', 'N/A')}")
        sys.exit(1)

    logger.info("=" * 70)


if __name__ == "__main__":
    main()
