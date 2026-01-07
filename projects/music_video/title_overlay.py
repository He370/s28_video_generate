import os
import sys
import json
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def add_title_overlay(idea_file: str, input_video: str, output_video: str):
    """
    Add title text overlay to the beginning of a video with fade in/out effects.
    
    The title will:
    - Fade in over 1 second
    - Display for 3 seconds
    - Fade out over 1 second
    - Total duration: 5 seconds
    
    Args:
        idea_file: Path to idea.json containing title and description
        input_video: Path to input video file
        output_video: Path to output video file with overlay
    """
    if not os.path.exists(idea_file):
        logging.error(f"Idea file {idea_file} not found.")
        return False
        
    if not os.path.exists(input_video):
        logging.error(f"Input video {input_video} not found.")
        return False
    
    with open(idea_file, 'r') as f:
        idea = json.load(f)
    
    genre = idea.get('genre', 'Music')
    
    # Escape special characters for FFmpeg drawtext filter
    # FFmpeg drawtext requires escaping: : \ ' [ ]
    def escape_ffmpeg_text(text):
        """Escape special characters for FFmpeg drawtext filter."""
        # Replace problematic characters
        text = text.replace('\\', '\\\\')  # Backslash must be first
        text = text.replace("'", "\\'")    # Single quote
        text = text.replace(':', '\\:')    # Colon
        text = text.replace('[', '\\[')    # Left bracket
        text = text.replace(']', '\\]')    # Right bracket
        return text
    
    genre_escaped = escape_ffmpeg_text(genre.upper())
    
    logging.info(f"Adding genre overlay: '{genre}'")
    
    # FFmpeg drawtext filter with fade effects
    # Positioning: centered horizontally and vertically
    # Font: Modern, using SF Pro or similar system font
    # Effects: fade in (0-1s), display (1-4s), fade out (4-5s)
    
    # Try to use a modern font
    font_options = [
        "/System/Library/Fonts/SFCompact.ttf",  # SF Compact (modern, clean)
        "/System/Library/Fonts/Supplemental/Futura.ttc",  # Futura (modern, geometric)
        "/System/Library/Fonts/Supplemental/Avenir.ttc",  # Avenir (modern, clean)
        "/System/Library/Fonts/Supplemental/Arial.ttf",  # Fallback
    ]
    
    font_file = None
    for font in font_options:
        if os.path.exists(font):
            font_file = font
            break
    
    if not font_file:
        font_file = "/System/Library/Fonts/Supplemental/Arial.ttf"
    
    logging.info(f"Using font: {font_file}")
    
    # Genre text (centered, large and prominent)
    genre_filter = (
        f"drawtext="
        f"text='{genre_escaped}':"
        f"fontfile={font_file}:"
        f"fontsize=72:"  # Large, prominent font
        f"fontcolor=white:"
        f"x=(w-text_w)/2:"
        f"y=(h-text_h)/2:"  # Centered vertically
        f"alpha='if(lt(t\\,1)\\, t\\, if(lt(t\\,4)\\, 1\\, if(lt(t\\,5)\\, 5-t\\, 0)))'"
    )
    
    # Use only genre filter
    video_filter = genre_filter
    
    # FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", video_filter,
        "-c:a", "copy",  # Copy audio stream
        "-c:v", "libx264",  # Re-encode video
        "-preset", "medium",  # Encoding speed/quality tradeoff
        "-crf", "18",  # High quality
        output_video
    ]
    
    try:
        logging.info("Applying title overlay with FFmpeg...")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"Title overlay added successfully: {output_video}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg failed: {e.stderr}")
        return False


if __name__ == "__main__":
    # Test with sample data
    import tempfile
    
    # Create a test idea.json
    test_idea = {
        "title": "RAIN & PIANO",
        "genre": "Ambient"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_idea, f)
        test_idea_file = f.name
    
    # Create a test video (dummy)
    test_input = "/tmp/test_input.mp4"
    test_output = "/tmp/test_output.mp4"
    
    # Create a simple test video if it doesn't exist
    if not os.path.exists(test_input):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=1920x1080:d=8",
            "-c:v", "libx264", "-t", "8", "-pix_fmt", "yuv420p",
            test_input
        ])
    
    add_title_overlay(test_idea_file, test_input, test_output)
    
    os.unlink(test_idea_file)
    print(f"Test output: {test_output}")
