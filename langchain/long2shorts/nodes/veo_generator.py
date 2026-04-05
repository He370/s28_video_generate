"""
veo_generator.py — Veo Generator Agent Node

Iterates through the short script timeline and generates video clips
for scenes with type == "veo" using the real Veo API via GeminiClient.
"""

import logging
import os
import sys
import tempfile

from PIL import Image

from langchain.long2shorts.state import VideoState

# Ensure project root is on path for imports
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger(__name__)


def veo_generator_node(state: VideoState) -> dict:
    """
    LangGraph node: Veo Generator — creates video clips for "veo" scenes
    using the real Veo API (GeminiClient).

    Input state keys:
        short_script, assets_dir

    Output state updates:
        veo_assets, error_message
    """
    logger.info("=" * 60)
    logger.info("🎥 VEO GENERATOR NODE — Starting")
    logger.info("=" * 60)

    short_script = state.get("short_script")
    assets_dir = state.get("assets_dir", "")

    if not short_script or "timeline" not in short_script:
        logger.error("No short_script or timeline found!")
        return {"error_message": "Veo Generator failed: no short_script"}

    timeline = short_script["timeline"]
    veo_assets = {}

    try:
        from video_generation_tool.gemini_client import GeminiClient

        # Initialize GeminiClient in production mode for real Veo calls
        client = GeminiClient(mode="prod")

        for i, scene in enumerate(timeline):
            if scene.get("type") != "veo":
                continue

            output_path = os.path.join(assets_dir, f"veo_clip_{i}.mp4")
            image_path = scene.get("original_image", "")
            veo_prompt = scene.get("veo_prompt", "")

            if not os.path.exists(image_path):
                logger.warning(f"  ⚠️ Image not found: {image_path}, skipping scene {i}")
                continue

            if not veo_prompt:
                logger.warning(f"  ⚠️ No veo_prompt for scene {i}, skipping")
                continue

            logger.info(f"  🎬 Generating Veo clip for scene {i}")
            logger.info(f"     Image: {os.path.basename(image_path)}")
            logger.info(f"     Prompt: {veo_prompt[:100]}...")

            try:
                # Convert image to JPEG for reliable API encoding
                pil_img = Image.open(image_path).convert("RGB")
                temp_jpg = os.path.join(assets_dir, f"_veo_input_{i}.jpg")
                pil_img.save(temp_jpg, "JPEG", quality=95)

                # Call the real Veo API
                client.generate_video(
                    prompt=veo_prompt,
                    output_path=output_path,
                    image_path=temp_jpg,
                )

                if os.path.exists(output_path):
                    veo_assets[i] = output_path
                    logger.info(f"  ✅ Veo clip saved: {output_path}")
                else:
                    logger.error(f"  ❌ Veo clip was not created for scene {i}")
            except Exception as scene_err:
                logger.error(f"  ❌ Veo generation failed for scene {i}: {scene_err}")
                # Continue with remaining scenes instead of aborting

        logger.info(f"📦 Veo assets generated: {len(veo_assets)} clips")
        for idx, path in veo_assets.items():
            logger.info(f"   Scene {idx}: {path}")

        logger.info("✅ VEO GENERATOR NODE — Complete")
        return {
            "veo_assets": veo_assets,
            "error_message": None,
        }

    except Exception as e:
        logger.error(f"❌ VEO GENERATOR NODE — Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error_message": f"Veo Generator failed: {e}",
        }
