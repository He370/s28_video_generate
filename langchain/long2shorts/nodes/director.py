"""
director.py — Director Agent Node

Uses Gemini (google-genai SDK) to condense a long-form video's segments
into a 30-40 second YouTube Shorts script.

Always makes a real API call to Gemini for script generation.
"""

import json
import logging
import os

from langchain.long2shorts.state import VideoState

logger = logging.getLogger(__name__)


DIRECTOR_SYSTEM_PROMPT = """You are an expert YouTube Shorts director. 
Your job is to take a long-form video's scene segments and condense them into 
a punchy, highly engaging 30-40 second vertical (9:16) YouTube Short.

RULES:
1. Extract a strong "HOOK" for the first 3 seconds — something shocking, mysterious, or curiosity-driven.
2. Total voiceover text MUST be under 80 English words.
3. Select only 4 to 6 key scenes from the provided segments.
4. Budget EXACTLY 3 scenes with "type": "veo" (AI-generated video clips). The rest MUST be "type": "static_pan".
5. CRITICAL: The very FIRST scene (index 0) MUST be "type": "veo" to hook the viewer.
6. CRITICAL: Within the FIRST THREE scenes (indices 0, 1, 2), there MUST be EXACTLY 2 "veo" scenes.
7. Total duration should be between 30-40 seconds.
8. Each scene duration should be between 4-8 seconds.
9. For "veo" scenes, write a dynamic, cinematic Veo prompt describing camera movement and action.
10. For "static_pan" scenes, set veo_prompt to an empty string.
11. Use the original_image path from the input segments — do NOT invent paths.

OUTPUT FORMAT: Return ONLY valid JSON (no markdown fencing) with this exact schema:
{
  "total_duration": <int>,
  "timeline": [
    {
      "type": "veo" or "static_pan",
      "duration": <int>,
      "voiceover": "Sentence for this scene...",
      "original_image": "/absolute/path/to/img.png",
      "veo_prompt": "Dynamic prompt for Veo if type is veo, else empty string"
    }
  ]
}
"""


def director_node(state: VideoState) -> dict:
    """
    LangGraph node: Director Agent — condenses long-form story into a short script.

    Always makes a real Gemini API call to generate the short script.

    Input state keys:
        input_segments, style_category, input_video_dir

    Output state updates:
        short_script, error_message
    """
    logger.info("=" * 60)
    logger.info("🎬 DIRECTOR NODE — Starting")
    logger.info("=" * 60)

    input_segments = state.get("input_segments", [])
    style_category = state.get("style_category", "General")
    input_video_dir = state.get("input_video_dir", "")
    assets_dir = state.get("assets_dir", "")

    if not input_segments:
        logger.error("No input segments provided!")
        return {"error_message": "Director failed: no input segments"}

    try:
        # Prepare the segments summary for the LLM
        segments_summary = []
        for i, seg in enumerate(input_segments):
            # Skip scene 0 as it is usually a title scene with text
            if i == 0:
                continue
                
            segments_summary.append({
                "index": i,
                "text": seg.get("text", ""),
                "image": seg.get("image", ""),
                "visual_idea": seg.get("image_prompt", seg.get("visual_idea", "")),
            })

        user_prompt = f"""
Style/Category: {style_category}
Source Video: {input_video_dir}

Here are all {len(segments_summary)} segments from the long-form video:

{json.dumps(segments_summary, indent=2)}

Now create a YouTube Shorts script following the rules.
Remember: EXACTLY 3 "veo" scenes total. First scene MUST be "veo". 
Exactly 2 "veo" scenes within the first three scenes.
4-6 total scenes. Under 80 words total voiceover. 30-40 seconds total.
Use the actual image paths from the segments above.
"""

        # ── Always call Gemini API ──
        from google import genai
        from google.genai import types

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        client = genai.Client(api_key=api_key)

        # Use the text model from constants
        from video_generation_tool.constants import GEMINI_TEXT_MODEL

        logger.info(f"Calling Gemini ({GEMINI_TEXT_MODEL}) for script generation...")

        response = client.models.generate_content(
            model=GEMINI_TEXT_MODEL,
            contents=f"{DIRECTOR_SYSTEM_PROMPT}\n\n{user_prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        response_text = response.text.strip()
        logger.info(f"Raw Gemini response:\n{response_text}")

        # Parse JSON response with extra robustness
        try:
            short_script = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find the first complete JSON object/array
            import re
            match = re.search(r'(\{.*\}|\[.*\])', response_text, re.DOTALL)
            if match:
                short_script = json.loads(match.group(0))
            else:
                raise

        # Handle case where Gemini returns a JSON array instead of object
        if isinstance(short_script, list) and len(short_script) > 0:
            short_script = short_script[0]

        # Validate the response structure
        if "timeline" not in short_script:
            raise ValueError("Missing 'timeline' in response")

        timeline = short_script["timeline"]
        veo_count = sum(1 for s in timeline if s.get("type") == "veo")
        total_words = sum(len(s.get("voiceover", "").split()) for s in timeline)

        logger.info(f"📋 Script Summary:")
        logger.info(f"   Scenes: {len(timeline)}")
        logger.info(f"   Veo scenes: {veo_count}")
        logger.info(f"   Total voiceover words: {total_words}")
        logger.info(f"   Total duration: {short_script.get('total_duration', 'N/A')}s")

        # Save the script to assets
        script_output_path = os.path.join(assets_dir, "short_script.json")
        with open(script_output_path, "w") as f:
            json.dump(short_script, f, indent=2)
        logger.info(f"Script saved to {script_output_path}")

        logger.info("✅ DIRECTOR NODE — Complete")
        return {
            "short_script": short_script,
            "error_message": None,
        }

    except Exception as e:
        logger.error(f"❌ DIRECTOR NODE — Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error_message": f"Director failed: {e}",
        }
