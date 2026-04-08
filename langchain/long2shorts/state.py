"""
state.py — LangGraph State Definition for Long2Shorts

All nodes share this state container via TypedDict.
LangGraph automatically passes and merges state between nodes.
"""

from typing import TypedDict, Optional


class VideoState(TypedDict, total=False):
    """
    LangGraph state for the Long2Shorts pipeline.

    Fields are grouped by responsibility:
    - Input: source video data and style
    - Director Output: condensed short script
    - Veo Output: generated video asset paths
    - Audio Output: TTS audio and subtitle data
    - Assembly Output: final rendered video
    - Working Directory: output paths
    """

    # ── Input ──────────────────────────────────────────────────
    input_video_dir: str              # Path to video_XX directory (e.g. horror_story/output/video_84)
    input_segments: list              # Raw data: [{'image': '/path.png', 'text': '...', 'visual_idea': '...'}]
    style_category: str               # e.g., "Horror" or "Fairy Tale"
    dev_mode: bool                    # If true, runs nodes in dev/mock mode
    all_veo: bool                     # If true, all scenes use Veo clips (no static_pan)
    
    # ── Director Output ───────────────────────────────────────
    short_script: Optional[dict]      # The director's cut timeline
    # Schema:
    # {
    #   "total_duration": 35,
    #   "timeline": [
    #     {
    #       "type": "veo" | "static_pan",
    #       "duration": 5,
    #       "voiceover": "Sentence for this scene...",
    #       "original_image": "/absolute/path/to/img.png",
    #       "veo_prompt": "Dynamic prompt for Veo if type is veo, else empty string"
    #     }
    #   ]
    # }

    # ── Veo Output ────────────────────────────────────────────
    veo_assets: Optional[dict]        # Mapping of timeline index to generated Veo mp4 paths
    # e.g. {0: "/path/to/veo_0.mp4", 3: "/path/to/veo_3.mp4"}

    # ── Audio Output ──────────────────────────────────────────
    audio_assets: Optional[dict]      # Master TTS audio path and subtitle sync data
    # e.g. {"master_audio": "/path/to/master_audio.mp3",
    #        "subtitles": [(0.0, 2.0, "Word1"), (2.0, 4.5, "Word2"), ...]}

    # ── Assembly Output ───────────────────────────────────────
    final_video_path: Optional[str]   # The output path for the rendered vertical video

    # ── Working Directory ─────────────────────────────────────
    output_dir: str                   # Working output directory for this run
    assets_dir: str                   # Assets subdirectory within output_dir

    # ── Error Tracking ────────────────────────────────────────
    error_message: Optional[str]      # Error message if any step failed

    # ── BGM ────────────────────────────────────────────────────
    bgm_dir: Optional[str]            # Path to BGM directory for background music
