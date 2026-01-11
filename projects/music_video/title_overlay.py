import json
import logging
import os
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def add_title_overlay(idea_file: str, input_video: str, output_video: str):
    """
    Add title text overlay to the beginning of a video with fade in/out effects.
    Match the 'Vogue' visual style from the thumbnail generator.
    
    Style Guide:
    1. Main Title (Genre): Playfair Display, Large Size.
    2. Subtitle (Mood + MUSIC): Lato Light, Small Size, Wide Tracking.
    3. Layout: Stacked vertically, centered.
    4. Effect: Fade in/out, displaying for 5s total.
    
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
    
    genre = idea.get('genre', 'Music').strip().upper()
    mood = idea.get('mood', 'Relaxing').strip().upper()
    subtitle_text = f"{mood} MUSIC"
    
    # Escape special characters for FFmpeg drawtext filter
    def escape_ffmpeg_text(text):
        text = text.replace('\\', '\\\\')
        text = text.replace("'", "\\'")
        text = text.replace(':', '\\:')
        text = text.replace('[', '\\[')
        text = text.replace(']', '\\]')
        # Also need to escape commas in filter strings often
        text = text.replace(',', '\\,')
        return text
    
    genre_escaped = escape_ffmpeg_text(genre)
    subtitle_escaped = escape_ffmpeg_text(subtitle_text)
    
    logging.info(f"Adding overlay: Title='{genre}', Subtitle='{subtitle_text}'")
    
    # Font Selection
    title_font = "/Users/leo/Library/Fonts/PlayfairDisplay-VariableFont_wght.ttf"
    if not os.path.exists(title_font):
        title_font = "/System/Library/Fonts/Supplemental/Didot.ttc"
        if not os.path.exists(title_font):
            title_font = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"

    subtitle_font = "/Users/leo/Library/Fonts/Lato-Light.ttf"
    if not os.path.exists(subtitle_font):
        subtitle_font = "/System/Library/Fonts/Supplemental/Avenir.ttc"
        if not os.path.exists(subtitle_font):
             subtitle_font = "/System/Library/Fonts/Helvetica.ttc"

    logging.info(f"Fonts: Title='{title_font}', Subtitle='{subtitle_font}'")

    # Font Sizing Logic
    # We can't do perfect width calculation in FFmpeg like PIL, so we use heuristics.
    # Title roughly 160-200 size for 1080p
    # Subtitle roughly 1/4 of title
    
    title_size = 180
    # Adjust title size down if text is very long
    if len(genre) > 10:
        title_size = 140
    if len(genre) > 15:
        title_size = 110

    subtitle_size = int(title_size * 0.35) 
    
    # Position calculations
    # We want them stacked in the center.
    # Approx Gap
    gap = 20
    
    # Vertical Alignment
    # Since we can't easily query exact text height in filter_complex without complex setups,
    # we assume standard centering.
    # Title Y: (h/2) + gap
    # Subtitle Y: (h/2) - (title_ascent)
    
    # Simplified approach:
    # Subtitle at (H/2) - 60
    # Title at (H/2) + 20
    
    # Alpha fade expression
    # 0-1s: Fade In, 1-4s: Hold, 4-5s: Fade Out
    fade_expr = "if(lt(t,1),t,if(lt(t,4),1,if(lt(t,5),5-t,0)))"
    
    # Drawtext filters
    # 1. Subtitle (Top of stack)
    # Using expansion=normal to allow standard rendering.
    # text_align=center? drawtext doesn't handle multi-line alignment logic easily for separate drawtexts.
    # We position x=(w-text_w)/2 for both.
    
    # Note on Spacing: FFmpeg 'spacing' option (tracking) is available in relatively recent builds.
    # We assume it supports it. 'text_shaping=0' might be needed if using 'spacing'.
    
    # Subtitle Filter
    # "spacing" unit is pixels? or font units? Usually pixels.
    # Vogue look needs wide spacing for subtitle.
    # Let's approximate wide spacing: 10px?
    subtitle_tracking = 15
    
    subtitle_filter = (
        f"drawtext="
        f"text='{subtitle_escaped}':"
        f"fontfile='{subtitle_font}':"
        f"fontsize={subtitle_size}:"
        f"fontcolor=white:"
        f"x=(w-text_w)/2:"
        f"y=(h-text_h)/2 - {title_size/2} - {gap}:" # Move up relative to center
        f"alpha='{fade_expr}':"
        f"shadowcolor=black@0.5:shadowx=0:shadowy=0:box=0:boxborderw=0:" # Soft shadow hack? drawtext shadow is hard.
        # To get soft shadow, we usually need split->blur->overlay, which is complex.
        # We will stick to a semi-transparent 'glow' using multiple shadows or just a simple shadow for readability.
        f"shadowx=2:shadowy=2:shadowcolor=black@0.6" # Simple drop shadow for readability
    )
    
    # Title Filter
    title_filter = (
        f"drawtext="
        f"text='{genre_escaped}':"
        f"fontfile='{title_font}':"
        f"fontsize={title_size}:"
        f"fontcolor=white:"
        f"x=(w-text_w)/2:"
        f"y=(h-text_h)/2 + {gap}:" # Move down relative to center
        f"alpha='{fade_expr}':"
        f"shadowx=2:shadowy=2:shadowcolor=black@0.6"
    )
    
    # Combine Filters: [0:v]subtitle[tmp];[tmp]title[out]
    filter_complex = f"{subtitle_filter},{title_filter}"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", filter_complex,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        output_video
    ]
    
    try:
        logging.info("Applying Vogue-style title overlay with FFmpeg...")
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
        "genre": "Jazz",
        "mood": "Relaxing"
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
