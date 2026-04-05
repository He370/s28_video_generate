"""
audio_agent.py — Audio Agent Node (edge_tts)

Generates TTS audio per scene using edge_tts, then concatenates
them into a master audio file. Captures word-level timestamps
from edge_tts WordBoundary events for subtitle rendering.
"""

import asyncio
import json
import logging
import os
import tempfile

from langchain.long2shorts.state import VideoState

logger = logging.getLogger(__name__)

# edge_tts voice for YouTube Shorts narration
EDGE_TTS_VOICE = "en-US-ChristopherNeural"


async def _generate_scene_audio(
    text: str,
    output_path: str,
    voice: str = EDGE_TTS_VOICE,
) -> None:
    """
    Generate TTS audio for a single scene using edge_tts.

    Args:
        text: The voiceover text for this scene
        output_path: Where to save the .mp3
        voice: edge_tts voice name
    """
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def _compute_word_subtitles(voiceover: str, start_offset: float, audio_duration: float) -> list:
    """
    Generate word-level subtitle entries by evenly distributing words
    across the actual audio duration of a scene.

    Args:
        voiceover: The voiceover text for the scene
        start_offset: Cumulative start time in seconds
        audio_duration: Actual duration of TTS audio for this scene

    Returns:
        List of (start_sec, end_sec, word) tuples
    """
    words = voiceover.split()
    if not words or audio_duration <= 0:
        return []

    time_per_word = audio_duration / len(words)
    subtitles = []
    current = start_offset

    for word in words:
        end = current + time_per_word
        subtitles.append((round(current, 3), round(end, 3), word))
        current = end

    return subtitles



def _concat_audio_files(audio_files: list, output_path: str):
    """
    Concatenate multiple audio files into a single master audio using ffmpeg.

    Args:
        audio_files: List of paths to individual scene audio files
        output_path: Where to save the concatenated audio
    """
    import subprocess

    if len(audio_files) == 1:
        # Just copy the single file
        import shutil
        shutil.copy2(audio_files[0], output_path)
        return

    # Create a temporary file list for ffmpeg concat
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for audio_file in audio_files:
            f.write(f"file '{audio_file}'\n")
        concat_list = f.name

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list,
                "-c", "copy",
                output_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    finally:
        os.unlink(concat_list)


def _get_audio_duration(path: str) -> float:
    """Get duration of an audio file in seconds using ffprobe."""
    import subprocess
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return float(result.stdout.decode().strip())
    except Exception:
        return 0.0


def audio_agent_node(state: VideoState) -> dict:
    """
    LangGraph node: Audio Agent — generates TTS audio using edge_tts.

    Generates audio per scene, captures word-level timestamps,
    and concatenates into a master audio file.

    Input state keys:
        short_script, assets_dir

    Output state updates:
        audio_assets, error_message
    """
    logger.info("=" * 60)
    logger.info("🎙️ AUDIO AGENT NODE — Starting")
    logger.info("=" * 60)

    short_script = state.get("short_script")
    assets_dir = state.get("assets_dir", "")

    if not short_script or "timeline" not in short_script:
        logger.error("No short_script or timeline found!")
        return {"error_message": "Audio Agent failed: no short_script"}

    timeline = short_script["timeline"]

    try:
        # ── Generate TTS per scene ──
        scene_audio_files = []
        all_subtitles = []  # [(start_sec, end_sec, word), ...]
        cumulative_offset = 0.0  # Track total elapsed time across scenes

        async def _generate_all_scenes():
            nonlocal cumulative_offset

            for i, scene in enumerate(timeline):
                voiceover = scene.get("voiceover", "").strip()
                if not voiceover:
                    # No voiceover — just advance the offset by scene duration
                    cumulative_offset += scene.get("duration", 5)
                    continue

                scene_audio_path = os.path.join(assets_dir, f"tts_scene_{i}.mp3")

                logger.info(f"  🎙️ Scene {i}: \"{voiceover[:60]}...\"")

                # Generate TTS audio
                await _generate_scene_audio(
                    voiceover, scene_audio_path, EDGE_TTS_VOICE
                )

                scene_audio_files.append(scene_audio_path)

                # Get actual audio duration
                scene_audio_duration = _get_audio_duration(scene_audio_path)
                word_count = len(voiceover.split())
                logger.info(f"     Audio duration: {scene_audio_duration:.2f}s, Words: {word_count}")

                # Compute word-level subtitles from voiceover text + actual audio duration
                scene_subs = _compute_word_subtitles(voiceover, cumulative_offset, scene_audio_duration)
                all_subtitles.extend(scene_subs)

                # Use actual audio duration for offset
                cumulative_offset += scene_audio_duration
                
                # Update the scene's duration to match the audio
                scene["duration"] = max(scene_audio_duration, 4.0)

        asyncio.run(_generate_all_scenes())

        if not scene_audio_files:
            raise ValueError("No audio files generated — check voiceover text")

        # ── Concatenate all scene audio into master ──
        master_audio_path = os.path.join(assets_dir, "master_audio.mp3")
        logger.info(f"  🔗 Concatenating {len(scene_audio_files)} audio files...")
        _concat_audio_files(scene_audio_files, master_audio_path)

        master_duration = _get_audio_duration(master_audio_path)
        logger.info(f"🎵 Master audio: {master_audio_path} ({master_duration:.2f}s)")
        logger.info(f"📑 Subtitle entries: {len(all_subtitles)}")

        # Save subtitles to JSON for debugging
        subtitles_path = os.path.join(assets_dir, "subtitles.json")
        with open(subtitles_path, "w") as f:
            json.dump(all_subtitles, f, indent=2)
        logger.info(f"📝 Subtitles saved to: {subtitles_path}")

        audio_result = {
            "master_audio": master_audio_path,
            "subtitles": all_subtitles,
        }

        logger.info("✅ AUDIO AGENT NODE — Complete")
        return {
            "short_script": short_script,
            "audio_assets": audio_result,
            "error_message": None,
        }

    except Exception as e:
        logger.error(f"❌ AUDIO AGENT NODE — Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error_message": f"Audio Agent failed: {e}",
        }
