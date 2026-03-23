"""
reviewer.py — Aesthetic Reviewer Node

Uses Gemini Vision to evaluate the quality of generated visuals.
Routes the graph based on the review result:
- Pass: End successfully
- Fail + retries remaining: Loop back to Planner
- Fail + max retries exceeded: End with controlled error
"""

import logging

from langchain.music_video.state import VideoGenerationState
from langchain.music_video.tools.review_tools import tool_review_visual_quality

logger = logging.getLogger(__name__)


def reviewer_node(state: VideoGenerationState) -> dict:
    """
    LangGraph node: Review the quality of generated visual assets.

    Input state keys used:
        cover_image_path, seamless_loop_path, idea, dev_mode,
        retry_count, error_message

    Output state updates:
        review_passed, review_feedback, retry_count, error_message
    """
    logger.info("=" * 60)
    logger.info("👁️ REVIEWER NODE — Starting")
    logger.info("=" * 60)

    retry_count = state.get("retry_count", 0)
    dev_mode = state.get("dev_mode", False)
    idea = state.get("idea", {})

    # If there was a generate/plan error, auto-fail the review
    if state.get("error_message"):
        logger.warning(f"Previous error detected: {state['error_message']}")
        new_retry = retry_count + 1
        max_retries = state.get("max_retries", 2)

        if new_retry >= max_retries:
            logger.error(f"❌ Max retries ({max_retries}) exceeded. Giving up.")
            return {
                "review_passed": False,
                "review_feedback": f"Pipeline error after {new_retry} attempts: {state['error_message']}",
                "retry_count": new_retry,
                "error_message": f"Max retries exceeded. Last error: {state['error_message']}",
            }

        logger.info(f"🔄 Will retry (attempt {new_retry + 1}/{max_retries})")
        return {
            "review_passed": False,
            "review_feedback": f"Pipeline error: {state['error_message']}. Please try a different theme/genre.",
            "retry_count": new_retry,
            "error_message": None,  # Clear error for retry
        }

    # Run the visual quality review
    mood = idea.get("mood", state.get("mood", "Unknown"))
    theme = idea.get("theme", "Unknown")
    cover_image_path = state.get("cover_image_path")
    seamless_loop_path = state.get("seamless_loop_path")

    passed, feedback = tool_review_visual_quality(
        cover_image_path=cover_image_path,
        seamless_loop_path=seamless_loop_path,
        mood=mood,
        theme=theme,
        dev_mode=dev_mode,
    )

    if passed:
        logger.info("✅ REVIEWER NODE — Quality check PASSED")
        return {
            "review_passed": True,
            "review_feedback": feedback,
            "retry_count": retry_count,
        }
    else:
        new_retry = retry_count + 1
        max_retries = state.get("max_retries", 2)
        logger.warning(f"⚠️ REVIEWER NODE — Quality check FAILED: {feedback}")
        logger.info(f"   Retry count: {new_retry}/{max_retries}")

        if new_retry >= max_retries:
            logger.error(f"❌ Max retries ({max_retries}) exceeded after review failure.")
            return {
                "review_passed": False,
                "review_feedback": feedback,
                "retry_count": new_retry,
                "error_message": f"Quality review failed after {new_retry} attempts: {feedback}",
            }

        return {
            "review_passed": False,
            "review_feedback": feedback,
            "retry_count": new_retry,
            "error_message": None,
        }
