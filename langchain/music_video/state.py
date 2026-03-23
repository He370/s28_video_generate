"""
VideoGenerationState — LangGraph 状态定义

所有节点共享的状态容器，使用 TypedDict 定义。
LangGraph 会在节点间自动传递和合并状态。
"""

from typing import TypedDict, Optional, List, Dict, Any


class VideoGenerationState(TypedDict, total=False):
    """
    LangGraph state for the Music Video generation pipeline.

    Fields are grouped by responsibility:
    - User Input: mood, genre, duration, flags
    - Planner Output: idea dict, selected tracks
    - Generator Output: file paths for each asset
    - Reviewer Output: review result and feedback
    - Control Flow: retry_count, max_retries, error_message
    - Working Directory: output_dir, assets_dir
    """

    # ── User Input ──────────────────────────────────────────
    mood: str                              # Desired mood (e.g. "Relaxing")
    genre: str                             # Desired genre (e.g. "Jazz")
    duration_hours: int                    # Video duration in hours
    enable_veo: bool                       # Use Veo for video generation
    dev_mode: bool                         # Development mode (dummy generation)

    # ── Planner Output ──────────────────────────────────────
    idea: Optional[Dict[str, Any]]         # Full idea.json content
    selected_tracks: Optional[List[Dict[str, Any]]]  # Selected music tracks

    # ── Generator Output (file paths) ──────────────────────
    cover_image_path: Optional[str]        # Cover image
    video_loop_path: Optional[str]         # Raw video loop (8s)
    seamless_loop_path: Optional[str]      # Seamless loop after cut-swap-fade
    video_with_title_path: Optional[str]   # Loop with title overlay
    thumbnail_path: Optional[str]          # YouTube thumbnail
    final_audio_path: Optional[str]        # Assembled audio track
    final_video_path: Optional[str]        # Final rendered video

    # ── Reviewer Output ─────────────────────────────────────
    review_passed: bool                    # Whether quality review passed
    review_feedback: Optional[str]         # LLM feedback for retry guidance

    # ── Control Flow ────────────────────────────────────────
    retry_count: int                       # Current retry attempt (starts at 0)
    max_retries: int                       # Threshold before giving up (default 2)
    error_message: Optional[str]           # Error message if any step failed

    # ── Working Directory ───────────────────────────────────
    output_dir: str                        # Video-specific output directory
    assets_dir: str                        # Assets subdirectory
