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

_SMART_CROP_PROMPT = """\
This image will be cropped from 16:9 landscape to 9:16 portrait (vertical). \
Only a narrow vertical strip (about 56% of the height's width) will be kept.

Analyze the image and determine the best HORIZONTAL position for the crop \
so that the main subject or focal point is preserved.

Return a single decimal number between 0.0 and 1.0 where:
- 0.0 = crop the leftmost strip
- 0.5 = crop the center strip
- 1.0 = crop the rightmost strip

Reply with ONLY the number, nothing else. Example: 0.35"""


def _get_smart_crop_position(client, pil_img) -> float:
    """Ask Gemini to suggest the best horizontal crop position for 9:16.

    Args:
        client: GeminiClient instance (already initialised).
        pil_img: PIL Image in RGB mode.

    Returns:
        Float between 0.0 and 1.0 representing the horizontal crop anchor.
    """
    from google.genai import types

    # Downscale for faster API response — we only need composition info
    thumb = pil_img.copy()
    thumb.thumbnail((512, 512))

    response = client.client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[_SMART_CROP_PROMPT, thumb],
        config=types.GenerateContentConfig(
            temperature=0.0,
            http_options=types.HttpOptions(timeout=30_000),
        ),
    )
    raw = response.text.strip()
    value = float(raw)
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"Crop position {value} out of range [0, 1]")
    return value



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

        # Initialize GeminiClient in requested mode
        mode = "dev" if state.get("dev_mode", False) else "prod"
        client = GeminiClient(mode=mode)

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
                # Convert image to RGB
                pil_img = Image.open(image_path).convert("RGB")
                img_w, img_h = pil_img.size
                
                # Smart crop to 9:16 — ask Gemini for optimal horizontal position
                target_ratio = 9.0 / 16.0
                current_ratio = img_w / img_h
                
                if current_ratio > target_ratio:
                    new_w = int(img_h * target_ratio)
                    # Smart crop: use Gemini to find best horizontal position
                    crop_position = 0.5  # default to center
                    try:
                        crop_position = _get_smart_crop_position(client, pil_img)
                        logger.info(f"     🎯 Smart crop position: {crop_position:.2f}")
                    except Exception as crop_err:
                        logger.warning(f"     ⚠️ Smart crop failed, falling back to center: {crop_err}")
                        crop_position = 0.5
                    
                    max_left = img_w - new_w
                    left = int(max_left * crop_position)
                    left = max(0, min(left, max_left))
                    pil_img = pil_img.crop((left, 0, left + new_w, img_h))
                else:
                    new_h = int(img_w / target_ratio)
                    top = (img_h - new_h) // 2
                    pil_img = pil_img.crop((0, top, img_w, top + new_h))
                
                # Save as JPEG for reliable API encoding
                temp_jpg = os.path.join(assets_dir, f"_veo_input_{i}.jpg")
                pil_img.save(temp_jpg, "JPEG", quality=95)

                if state.get("dev_mode", False):
                    # use moviepy to make it a dummy directly
                    import subprocess
                    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", temp_jpg, "-c:v", "libx264", "-t", "5", "-pix_fmt", "yuv420p", output_path], check=True)
                else:
                    # Call the real Veo API with retry
                    from video_generation_tool.utils import generate_video_with_retry
                    generate_video_with_retry(
                        client=client,
                        prompt=veo_prompt,
                        output_path=output_path,
                        image_path=temp_jpg,
                        aspect_ratio="9:16",
                        max_retries=1,
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
