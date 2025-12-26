import os
import sys
import json
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

AUDIO_FILE = 'final_audio.mp3'
VIDEO_LOOP = 'visuals_loop.mp4'
OUTPUT_VIDEO = 'final_video.mp4'



def assemble_final_video(audio_file: str, video_loop: str, output_video: str, duration_hours: int = 1):
    if not os.path.exists(audio_file):
        logging.error(f"Audio file {audio_file} not found.")
        return
    if not os.path.exists(video_loop):
        logging.error(f"Video loop {video_loop} not found.")
        return

    logging.info(f"Assembling final video with ffmpeg for {duration_hours} hours...")

    duration_seconds = duration_hours * 3600

    # Command explanation:
    # -stream_loop -1 -i video: Infinite video loop
    # -stream_loop -1 -i audio: Infinite audio loop (just in case audio is slightly short, though assembler should handle it)
    # -t duration: Strict duration cut
    # -c:v copy: Copy video stream (fast)
    # -c:a copy: Copy audio stream (fast)
    # Note: re-encoding might be safer for strict -t if keyframes don't align, but copy is much faster.
    
    cmd = [
        "ffmpeg",
        "-stream_loop", "-1",
        "-i", video_loop,
        "-stream_loop", "-1", 
        "-i", audio_file,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "copy",
        "-t", str(duration_seconds),
        "-y",
        output_video
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Final video created at {output_video}")
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg failed: {e}")

if __name__ == "__main__":
    assemble_final_video('final_audio.mp3', 'visuals_loop.mp4', 'final_video.mp4')


