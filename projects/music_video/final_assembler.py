import os
import sys
import json
import logging
import subprocess

import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binary_path(binary_name):
    """Find the absolute path to a binary, with specific checks for Homebrew."""
    path = shutil.which(binary_name)
    if path:
        return path
    
    # Common fallback locations for Mac (especially Homebrew on Apple Silicon)
    possible_paths = [
        f"/opt/homebrew/bin/{binary_name}",
        f"/usr/local/bin/{binary_name}",
        f"/usr/bin/{binary_name}"
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            return p
            
    return binary_name

# Define command paths globally
FFMPEG_CMD = get_binary_path("ffmpeg")
FFPROBE_CMD = get_binary_path("ffprobe")

AUDIO_FILE = 'final_audio.mp3'
VIDEO_LOOP = 'visuals_loop.mp4'
OUTPUT_VIDEO = 'final_video.mp4'



def assemble_final_video(audio_file: str, video_loop: str, output_video: str, duration_hours: int = 1, intro_video: str = None):
    if not os.path.exists(audio_file):
        logging.error(f"Audio file {audio_file} not found.")
        return
    if not os.path.exists(video_loop):
        logging.error(f"Video loop {video_loop} not found.")
        return
    if intro_video and not os.path.exists(intro_video):
        logging.error(f"Intro video {intro_video} not found. Proceeding without it.")
        intro_video = None

    logging.info(f"Assembling final video with ffmpeg for {duration_hours} hours...")

    duration_seconds = duration_hours * 3600
    
    # Get duration of video loop and intro to calculate loops needed
    try:
        # Get video loop duration
        result = subprocess.run([
            FFPROBE_CMD, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_loop
        ], capture_output=True, text=True, check=True)
        loop_duration = float(result.stdout.strip())
        
        intro_duration = 0
        if intro_video:
            result = subprocess.run([
                FFPROBE_CMD, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", intro_video
            ], capture_output=True, text=True, check=True)
            intro_duration = float(result.stdout.strip())
            
    except Exception as e:
        logging.error(f"Failed to get video durations: {e}")
        return

    # If intro_video is provided, we use the concat demuxer
    if intro_video:
        # Calculate how many loops we need
        remaining_duration = duration_seconds - intro_duration
        if remaining_duration < 0:
            remaining_duration = 0
            
        loops_needed = int(remaining_duration / loop_duration) + 1
        
        logging.info(f"Intro duration: {intro_duration}s, Loop duration: {loop_duration}s")
        logging.info(f"Repeats needed: {loops_needed}")
        
        # Create concat file
        concat_file = os.path.join(os.path.dirname(output_video), "concat_list.txt")
        with open(concat_file, "w") as f:
            f.write(f"file '{intro_video}'\n")
            for _ in range(loops_needed):
                f.write(f"file '{video_loop}'\n")
        
        cmd = [
            FFMPEG_CMD,
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-stream_loop", "-1",
            "-i", audio_file,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",     # Re-encode audio to AAC to ensure proper looping and timestamping
            "-b:a", "192k",    # Good quality audio
            "-t", str(duration_seconds),
            "-y",
            output_video
        ]
        
    else:
        # Traditional stream_loop approach
        cmd = [
            FFMPEG_CMD,
            "-stream_loop", "-1",
            "-i", video_loop,
            "-stream_loop", "-1", 
            "-i", audio_file,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration_seconds),
            "-y",
            output_video
        ]
    
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Final video created at {output_video}")
        # Cleanup
        if intro_video and os.path.exists(concat_file):
            os.remove(concat_file)
            
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg failed: {e}")

if __name__ == "__main__":
    # Test
    # assemble_final_video('final_audio.mp3', 'visuals_loop.mp4', 'final_video.mp4', intro_video='visuals_loop_with_title.mp4')
    pass


