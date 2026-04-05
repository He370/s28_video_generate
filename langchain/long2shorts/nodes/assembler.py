"""
assembler.py — Assembler Agent Node (MoviePy)

Uses moviepy to assemble the final vertical (9:16) YouTube Short video.
No LLM calls — pure video composition logic.

Resolution: 1080x1920 (9:16), fps=24

Features:
- static_pan: blurred bg + centered 16:9 image with smooth ffmpeg zoompan
- veo: center-cropped to 9:16 and trimmed
- Subtitles: chunked word-by-word, bold Impact font, YouTube Shorts style
- BGM: random track from project BGM directory, mixed under TTS
"""

import glob
import logging
import os
import random
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageFilter

from langchain.long2shorts.state import VideoState

logger = logging.getLogger(__name__)

# Output specs
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
OUTPUT_FPS = 24

# ── Subtitle styling (YouTube Shorts style) ──
SUBTITLE_FONT = "Impact"
SUBTITLE_FONT_SIZE = 85
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "black"
SUBTITLE_STROKE_WIDTH = 5
SUBTITLE_Y_POSITION = 0.70  # 70% from top (lower third)
SUBTITLE_WORDS_PER_CHUNK = 3  # Group words into 3-word chunks

# ── BGM mixing ──
BGM_VOLUME = 0.10  # 10% volume for background music


def _create_static_pan_clip(image_path: str, duration: float, assets_dir: str, scene_index: int):
    """
    Creates a vertical (9:16) clip from a 16:9 image with:
    - Background: center-cropped to fill 1080x1920, heavy Gaussian blur
    - Foreground: smooth Ken Burns zoom via ffmpeg zoompan filter

    Uses ffmpeg zoompan for buttery smooth zoom instead of per-frame PIL resize.

    Args:
        image_path: Path to the 16:9 source image
        duration: Duration of the clip in seconds
        assets_dir: Directory for intermediate files
        scene_index: Scene index for unique filenames

    Returns:
        A CompositeVideoClip of the layered result
    """
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

    # Load original image
    pil_img = Image.open(image_path).convert("RGB")
    img_w, img_h = pil_img.size

    # ── Background layer: center-crop to 9:16, heavy blur ──
    target_ratio = OUTPUT_WIDTH / OUTPUT_HEIGHT  # 0.5625

    current_ratio = img_w / img_h
    if current_ratio > target_ratio:
        new_w = int(img_h * target_ratio)
        left = (img_w - new_w) // 2
        bg_crop = pil_img.crop((left, 0, left + new_w, img_h))
    else:
        new_h = int(img_w / target_ratio)
        top = (img_h - new_h) // 2
        bg_crop = pil_img.crop((0, top, img_w, top + new_h))

    bg_resized = bg_crop.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.LANCZOS)
    bg_blurred = bg_resized.filter(ImageFilter.GaussianBlur(radius=30))
    bg_array = np.array(bg_blurred).astype(float) * 0.4
    bg_array = bg_array.clip(0, 255).astype(np.uint8)

    bg_clip = ImageClip(bg_array).with_duration(duration)

    # ── Foreground layer: smooth zoompan via ffmpeg ──
    fg_w = OUTPUT_WIDTH
    fg_h = int(fg_w * img_h / img_w)  # Maintain aspect ratio

    # Ensure even dimensions (required by x264)
    fg_w = fg_w + (fg_w % 2)
    fg_h = fg_h + (fg_h % 2)

    # Prepare a resized source image for ffmpeg
    fg_resized = pil_img.resize((fg_w, fg_h), Image.LANCZOS)
    temp_fg_img = os.path.join(assets_dir, f"_fg_scene_{scene_index}.png")
    fg_resized.save(temp_fg_img)

    # Use ffmpeg zoompan for smooth zoom (1.0x → 1.08x)
    total_frames = int(duration * OUTPUT_FPS)
    temp_fg_video = os.path.join(assets_dir, f"_fg_zoom_{scene_index}.mp4")

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", temp_fg_img,
                "-vf", (
                    f"zoompan=z='1+0.08*in/{total_frames}'"
                    f":x='iw/2-(iw/zoom/2)'"
                    f":y='ih/2-(ih/zoom/2)'"
                    f":d={total_frames}"
                    f":s={fg_w}x{fg_h}"
                    f":fps={OUTPUT_FPS}"
                ),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-t", str(duration),
                temp_fg_video,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg zoompan error: {e.stderr.decode()[:500]}")
        raise

    fg_clip = VideoFileClip(temp_fg_video).subclipped(0, duration)

    # Position foreground centered vertically
    y_pos = (OUTPUT_HEIGHT - fg_h) // 2
    fg_clip = fg_clip.with_position(("center", y_pos))

    # Composite
    composite = CompositeVideoClip(
        [bg_clip, fg_clip],
        size=(OUTPUT_WIDTH, OUTPUT_HEIGHT),
    )

    return composite


def _create_veo_clip(video_path: str, duration: float):
    """
    Creates a vertical (9:16) clip from a Veo-generated video.
    Center-crops to 9:16 if necessary, trims to requested duration.
    """
    from moviepy import VideoFileClip

    clip = VideoFileClip(video_path)

    if clip.duration > duration:
        clip = clip.subclipped(0, duration)

    clip_w, clip_h = clip.size
    target_ratio = OUTPUT_WIDTH / OUTPUT_HEIGHT

    current_ratio = clip_w / clip_h
    if abs(current_ratio - target_ratio) > 0.01:
        if current_ratio > target_ratio:
            new_w = int(clip_h * target_ratio)
            x_offset = (clip_w - new_w) // 2
            clip = clip.cropped(x1=x_offset, x2=x_offset + new_w)
        else:
            new_h = int(clip_w / target_ratio)
            y_offset = (clip_h - new_h) // 2
            clip = clip.cropped(y1=y_offset, y2=y_offset + new_h)

    clip = clip.resized((OUTPUT_WIDTH, OUTPUT_HEIGHT))
    return clip


def _create_subtitle_clips(subtitles: list, video_duration: float):
    """
    Create subtitle TextClips from word-level timestamps.

    Groups words into chunks of SUBTITLE_WORDS_PER_CHUNK and displays
    them as bold text in the lower third, YouTube Shorts style.

    Uses `method='label'` so text is never clipped by a bounding box.

    Args:
        subtitles: List of (start_sec, end_sec, word) tuples
        video_duration: Total video duration for clamping

    Returns:
        List of positioned TextClips
    """
    from moviepy import TextClip

    if not subtitles:
        return []

    text_clips = []

    # Group words into chunks
    chunks = []
    current_chunk_words = []
    current_chunk_start = None
    current_chunk_end = None

    for start, end, word in subtitles:
        if current_chunk_start is None:
            current_chunk_start = start

        current_chunk_words.append(word)
        current_chunk_end = end

        if len(current_chunk_words) >= SUBTITLE_WORDS_PER_CHUNK:
            chunks.append({
                "text": " ".join(current_chunk_words).upper(),
                "start": current_chunk_start,
                "end": current_chunk_end,
            })
            current_chunk_words = []
            current_chunk_start = None
            current_chunk_end = None

    # Don't forget the last partial chunk
    if current_chunk_words:
        chunks.append({
            "text": " ".join(current_chunk_words).upper(),
            "start": current_chunk_start,
            "end": current_chunk_end,
        })

    logger.info(f"  📝 Creating {len(chunks)} subtitle chunks from {len(subtitles)} words")

    y_pos = int(OUTPUT_HEIGHT * SUBTITLE_Y_POSITION)

    for chunk in chunks:
        start = max(0, chunk["start"])
        end = min(video_duration, chunk["end"])
        duration = end - start

        if duration <= 0:
            continue

        try:
            txt_clip = TextClip(
                text=chunk["text"],
                font=SUBTITLE_FONT,
                font_size=SUBTITLE_FONT_SIZE,
                color=SUBTITLE_COLOR,
                stroke_color=SUBTITLE_STROKE_COLOR,
                stroke_width=SUBTITLE_STROKE_WIDTH,
                method="label",  # 'label' renders full text without clipping
                text_align="center",
            )
            txt_clip = (
                txt_clip
                .with_duration(duration)
                .with_start(start)
                .with_position(("center", y_pos))
            )
            text_clips.append(txt_clip)
        except Exception as e:
            logger.warning(f"  ⚠️ Failed to create subtitle clip: {e}")
            continue

    return text_clips


def _select_bgm(bgm_dir: str) -> str:
    """
    Select a random BGM file from the project's BGM directory.

    Args:
        bgm_dir: Path to the BGM directory

    Returns:
        Path to a randomly selected .mp3 file, or empty string if none found
    """
    if not bgm_dir or not os.path.isdir(bgm_dir):
        return ""

    bgm_files = glob.glob(os.path.join(bgm_dir, "*.mp3"))
    if not bgm_files:
        return ""

    selected = random.choice(bgm_files)
    logger.info(f"  🎵 Selected BGM: {os.path.basename(selected)}")
    return selected


def assembler_node(state: VideoState) -> dict:
    """
    LangGraph node: Assembler — composites all clips into a final vertical video.

    No LLM calls. Pure MoviePy composition.

    Input state keys:
        short_script, veo_assets, audio_assets, output_dir, assets_dir, bgm_dir

    Output state updates:
        final_video_path, error_message
    """
    logger.info("=" * 60)
    logger.info("🔧 ASSEMBLER NODE — Starting")
    logger.info("=" * 60)

    short_script = state.get("short_script")
    veo_assets = state.get("veo_assets") or {}
    audio_assets = state.get("audio_assets", {})
    output_dir = state.get("output_dir", "")
    assets_dir = state.get("assets_dir", "")
    bgm_dir = state.get("bgm_dir", "")

    if not short_script or "timeline" not in short_script:
        logger.error("No short_script or timeline found!")
        return {"error_message": "Assembler failed: no short_script"}

    timeline = short_script["timeline"]

    try:
        from moviepy import AudioFileClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips

        clips = []

        for i, scene in enumerate(timeline):
            scene_type = scene.get("type", "static_pan")
            duration = scene.get("duration", 5)
            image_path = scene.get("original_image", "")

            logger.info(f"  📎 Scene {i}: type={scene_type}, duration={duration}s")

            if scene_type == "veo" and i in veo_assets:
                veo_path = veo_assets[i]
                if os.path.exists(veo_path):
                    logger.info(f"     Loading Veo clip: {veo_path}")
                    clip = _create_veo_clip(veo_path, duration)
                    clips.append(clip)
                else:
                    logger.warning(f"     ⚠️ Veo clip missing, falling back to static_pan")
                    if os.path.exists(image_path):
                        clip = _create_static_pan_clip(image_path, duration, assets_dir, i)
                        clips.append(clip)
            else:
                if os.path.exists(image_path):
                    logger.info(f"     Creating static_pan from: {os.path.basename(image_path)}")
                    clip = _create_static_pan_clip(image_path, duration, assets_dir, i)
                    clips.append(clip)
                else:
                    logger.warning(f"     ⚠️ Image not found: {image_path}")

        if not clips:
            raise ValueError("No clips were generated — check image paths")

        # Concatenate all clips
        logger.info(f"  🎞️ Concatenating {len(clips)} clips...")
        final_clip = concatenate_videoclips(clips, method="compose")

        # ── Add subtitles ──
        subtitles = audio_assets.get("subtitles", [])
        if subtitles:
            logger.info(f"  📝 Adding subtitles ({len(subtitles)} words)...")
            subtitle_clips = _create_subtitle_clips(subtitles, final_clip.duration)
            if subtitle_clips:
                final_clip = CompositeVideoClip(
                    [final_clip] + subtitle_clips,
                    size=(OUTPUT_WIDTH, OUTPUT_HEIGHT),
                )
                logger.info(f"     Added {len(subtitle_clips)} subtitle chunks")
        else:
            logger.warning("  ⚠️ No subtitles data, rendering without subtitles")

        # ── Mix audio: TTS voiceover + BGM ──
        audio_layers = []

        # Layer 1: TTS voiceover
        master_audio_path = audio_assets.get("master_audio", "")
        if master_audio_path and os.path.exists(master_audio_path):
            logger.info(f"  🔊 Attaching voiceover: {master_audio_path}")
            tts_audio = AudioFileClip(master_audio_path)
            if tts_audio.duration > final_clip.duration:
                tts_audio = tts_audio.subclipped(0, final_clip.duration)
            audio_layers.append(tts_audio)
        else:
            logger.warning("  ⚠️ No master audio found")

        # Layer 2: BGM (if available)
        bgm_path = _select_bgm(bgm_dir)
        if bgm_path:
            logger.info(f"  🎶 Mixing BGM at {int(BGM_VOLUME * 100)}% volume")
            bgm_audio = AudioFileClip(bgm_path)
            # Loop or trim BGM to match video duration
            if bgm_audio.duration < final_clip.duration:
                # Loop the BGM
                loops_needed = int(final_clip.duration / bgm_audio.duration) + 1
                from moviepy import concatenate_audioclips
                bgm_audio = concatenate_audioclips([bgm_audio] * loops_needed)
            bgm_audio = bgm_audio.subclipped(0, final_clip.duration)
            bgm_audio = bgm_audio.with_volume_scaled(BGM_VOLUME)
            audio_layers.append(bgm_audio)

        # Combine audio layers
        if audio_layers:
            if len(audio_layers) == 1:
                final_clip = final_clip.with_audio(audio_layers[0])
            else:
                mixed_audio = CompositeAudioClip(audio_layers)
                final_clip = final_clip.with_audio(mixed_audio)

        # Render final video
        final_video_path = os.path.join(output_dir, "youtube_short.mp4")
        logger.info(f"  🎬 Rendering to: {final_video_path}")
        logger.info(f"     Resolution: {OUTPUT_WIDTH}x{OUTPUT_HEIGHT}")
        logger.info(f"     FPS: {OUTPUT_FPS}")
        logger.info(f"     Duration: {final_clip.duration:.1f}s")

        final_clip.write_videofile(
            final_video_path,
            fps=OUTPUT_FPS,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
        )

        logger.info(f"✅ ASSEMBLER NODE — Complete")
        logger.info(f"   Output: {final_video_path}")

        return {
            "final_video_path": final_video_path,
            "error_message": None,
        }

    except Exception as e:
        logger.error(f"❌ ASSEMBLER NODE — Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error_message": f"Assembler failed: {e}",
        }
