import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_seamless_loop(input_video: str, output_video: str, crossfade_duration: float = 0.5):
    """
    Create a seamless loop video using the "Cut, Swap, and Fade" technique.
    
    This technique:
    1. Splits the 8s video into two 4s segments
    2. Swaps their order (second half becomes first, first half becomes second)
    3. Applies crossfade transition at the swap point
    4. Outputs a seamless 8s loop
    
    This hides the loop point by ensuring the transition happens mid-action
    rather than at the natural start/end.
    
    Args:
        input_video: Path to input 8-second video
        output_video: Path to output seamless loop video
        crossfade_duration: Duration of crossfade in seconds (default 0.5s)
    """
    if not os.path.exists(input_video):
        logging.error(f"Input video {input_video} not found.")
        return False
    
    logging.info("Creating seamless loop using Cut, Swap, and Fade technique...")
    
    # Get video duration to verify it's 8 seconds
    try:
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_video
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        logging.info(f"Input video duration: {duration:.2f}s")
        
        if abs(duration - 8.0) > 0.5:
            logging.warning(f"Expected 8-second video, got {duration:.2f}s. Proceeding anyway...")
    except Exception as e:
        logging.warning(f"Could not verify video duration: {e}")
    
    # Calculate split point (middle of video)
    split_point = duration / 2 if 'duration' in locals() else 4.0
    
    # Temporary directory for intermediate files
    temp_dir = os.path.dirname(output_video)
    temp_first_half = os.path.join(temp_dir, "temp_first_half.mp4")
    temp_second_half = os.path.join(temp_dir, "temp_second_half.mp4")
    
    try:
        # Step 1: Split video into two halves
        logging.info(f"Splitting video at {split_point}s...")
        
        # Extract first half (0 to split_point)
        cmd_first = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-t", str(split_point),
            "-c:v", "libx264",  # Re-encode to avoid format issues
            "-preset", "fast",
            "-crf", "18",
            temp_first_half
        ]
        subprocess.run(cmd_first, check=True, capture_output=True)
        
        # Extract second half (split_point to end)
        cmd_second = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-ss", str(split_point),
            "-c:v", "libx264",  # Re-encode to avoid format issues
            "-preset", "fast",
            "-crf", "18",
            temp_second_half
        ]
        subprocess.run(cmd_second, check=True, capture_output=True)
        
        # Step 2: Swap and crossfade
        # We want: [second_half] crossfade [first_half]
        # Use xfade filter for smooth transition
        
        logging.info(f"Applying crossfade ({crossfade_duration}s)...")
        
        # The xfade filter requires both inputs to be re-encoded
        # Format: [0:v][1:v]xfade=transition=fade:duration=D:offset=O[v]
        # Offset is when the transition starts in the output timeline
        
        # Since second_half comes first, transition starts at (second_half_duration - crossfade_duration)
        transition_offset = split_point - crossfade_duration
        
        cmd_merge = [
            "ffmpeg", "-y",
            "-i", temp_second_half,
            "-i", temp_first_half,
            "-filter_complex",
            f"[0:v][1:v]xfade=transition=fade:duration={crossfade_duration}:offset={transition_offset}[v]",
            "-map", "[v]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            output_video
        ]
        
        subprocess.run(cmd_merge, check=True, capture_output=True)
        
        logging.info(f"Seamless loop created: {output_video}")
        
        # Cleanup temporary files
        if os.path.exists(temp_first_half):
            os.remove(temp_first_half)
        if os.path.exists(temp_second_half):
            os.remove(temp_second_half)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg failed: {e}")
        if e.stderr:
            logging.error(f"Error output: {e.stderr.decode()}")
        
        # Cleanup on error
        for temp_file in [temp_first_half, temp_second_half]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        return False
    except Exception as e:
        logging.error(f"Error creating seamless loop: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test with a sample video
    test_input = "/tmp/test_loop_input.mp4"
    test_output = "/tmp/test_loop_output.mp4"
    
    # Create a test 8-second video with changing colors
    # This helps visualize the swap and fade
    if not os.path.exists(test_input):
        logging.info("Creating test video...")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=blue:s=1920x1080:d=4",
            "-f", "lavfi",
            "-i", "color=c=red:s=1920x1080:d=4",
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]",
            "-map", "[v]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            test_input
        ])
    
    create_seamless_loop(test_input, test_output, crossfade_duration=0.5)
    print(f"Test output: {test_output}")
    print("The output should show: red (fading from blue) -> blue (second half swapped to front)")
