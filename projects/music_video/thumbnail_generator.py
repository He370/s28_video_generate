import json
import logging
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_text_dimensions(text, font, spacing=0):
    """Calculate the total width and height of text with letter spacing."""
    if not text:
        return 0, 0
    
    total_width = 0
    max_height = 0
    
    # Calculate width
    for i, char in enumerate(text):
        bbox = font.getbbox(char)
        # some fonts have offsets, but for simple width calc:
        # width = bbox[2] - bbox[0] -> No, getlength is better for tracking
        char_width = font.getlength(char)
        total_width += char_width
        
        # Add spacing (not after last char)
        if i < len(text) - 1:
            total_width += spacing
            
    # Calculate max height (roughly)
    # ascent + descent is safer
    ascent, descent = font.getmetrics()
    max_height = ascent + descent
    
    return total_width, max_height


def draw_text_with_spacing(draw, xy, text, font, spacing=0, fill="white"):
    """Draw text with specific letter spacing."""
    x, y = xy
    current_x = x
    
    for i, char in enumerate(text):
        draw.text((current_x, y), char, font=font, fill=fill)
        char_width = font.getlength(char)
        current_x += char_width + spacing


def create_soft_shadow(image_size, text_items, blur_radius=10):
    """
    Create a shadow layer with multiple text items.
    text_items format: [(text, font, xy, spacing), ...]
    """
    # Create a transparent mask
    mask = Image.new('RGBA', image_size, (0, 0, 0, 0))
    d = ImageDraw.Draw(mask)
    
    for text, font, xy, spacing in text_items:
        draw_text_with_spacing(d, xy, text, font, spacing, fill="black")
        
    # Apply Gaussian Blur
    shadow = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # Optional: Strengthen shadow by compositing it multiple times or adjusting alpha
    # But GaussianBlur reduces opacity, so maybe darken
    
    return shadow


def generate_thumbnail(idea_file: str, cover_image: str, output_path: str):
    """
    Generate a YouTube thumbnail using the 'Vogue' Magazine Look.
    
    Style Guide:
    1. Main Title (Genre): Serif font (Didot), Large, Standard/Tight tracking.
    2. Subtitle (Mood): Sans-Serif Light (Avenir), Small, EXTREMELY WIDE tracking.
    3. Effect: Soft Gaussian Shadow, no hard outlines.
    """
    if not os.path.exists(idea_file):
        logging.error(f"Idea file {idea_file} not found.")
        return False
        
    if not os.path.exists(cover_image):
        logging.error(f"Cover image {cover_image} not found.")
        return False
    
    with open(idea_file, 'r') as f:
        idea = json.load(f)
    
    genre = idea.get('genre', 'Music').strip().upper()
    mood = idea.get('mood', 'Relaxing').strip().upper()
    
    # Subtitle text: Mood + " MUSIC"
    subtitle_text = f"{mood} MUSIC"
    
    logging.info(f"Generating Vogue-style thumbnail for: '{genre}' (Title) & '{subtitle_text}' (Subtitle)")
    
    try:
        # 1. Image Setup
        img = Image.open(cover_image)
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        img = img.convert('RGBA')
        
        draw = ImageDraw.Draw(img)
        
        # 2. Font Selection
        # Main Title: Serif (Playfair Display)
        serif_font_path = "/Users/leo/Library/Fonts/PlayfairDisplay-VariableFont_wght.ttf"
        if not os.path.exists(serif_font_path):
             # Fallback
             serif_font_path = "/System/Library/Fonts/Supplemental/Didot.ttc"
            
        # Subtitle: Sans-Serif Light (Lato Light)
        sans_font_path = "/Users/leo/Library/Fonts/Lato-Light.ttf"
        if not os.path.exists(sans_font_path):
            # Fallback
            sans_font_path = "/System/Library/Fonts/Supplemental/Avenir.ttc"

        # 3. Layout Calculation
        
        CANVAS_WIDTH = 1280
        CANVAS_HEIGHT = 720
        
        # User requested text width to occupy 60% of the screen
        MAX_TEXT_WIDTH = int(CANVAS_WIDTH * 0.6)
        
        # ---- STEP A: Size the Main Title (Genre) ----
        # Target: Large, occupancy ~60-80% of width?
        # Start large and shrink
        title_font_size = 200 # Starting huge
        title_font = None
        title_width = 0
        title_height = 0
        
        # Create font object
        while title_font_size > 40:
            try:
                title_font = ImageFont.truetype(serif_font_path, title_font_size)
            except:
                title_font = ImageFont.load_default()
                break
                
            title_width, title_height = get_text_dimensions(genre, title_font, spacing=0)
            
            if title_width <= MAX_TEXT_WIDTH:
                break
            title_font_size -= 5
            
        logging.info(f"Title Font Size: {title_font_size}")
        
        # ---- STEP B: Size the Subtitle (Mood + Music) ----
        # Initial guess: Font size is significantly smaller (e.g., 1/3 or 1/4 of title)
        subtitle_font_size = int(title_font_size * 0.25)
        if subtitle_font_size < 24: subtitle_font_size = 24
        
        subtitle_font = ImageFont.truetype(sans_font_path, subtitle_font_size)
        
        # Calculate spacing needed to match title width
        raw_sub_width, sub_height = get_text_dimensions(subtitle_text, subtitle_font, spacing=0)
        
        # If possible, spread it out to match title width
        target_width = title_width
        
        if len(subtitle_text) > 1:
            req_spacing = (target_width - raw_sub_width) / (len(subtitle_text) - 1)
        else:
            req_spacing = 0
            
        # Max spacing constraint (avoid absurdity)
        max_spacing = subtitle_font_size * 3.0
        
        # Minimum spacing constraint to ensure "Vogue" look
        min_spacing = subtitle_font_size * 0.8
        
        subtitle_spacing = max(req_spacing, min_spacing)
        
        subtitle_width, _ = get_text_dimensions(subtitle_text, subtitle_font, spacing=subtitle_spacing)
        
        # Recalculate if subtitle is now wider than screen
        if subtitle_width > MAX_TEXT_WIDTH:
            if len(subtitle_text) > 1:
                subtitle_spacing = (MAX_TEXT_WIDTH - raw_sub_width) / (len(subtitle_text) - 1)
                subtitle_width = MAX_TEXT_WIDTH
        
        # ---- STEP C: Positioning ----
        # Center vertically as a block
        # Block Height = SubtitleH + Gap + TitleH
        GAP = title_font_size * 0.1 # Small gap
        
        total_block_height = sub_height + GAP + title_height
        
        # Vertically centered
        block_start_y = (CANVAS_HEIGHT - total_block_height) // 2
        
        # Title Position (Centered)
        title_x = (CANVAS_WIDTH - title_width) // 2
        title_y = block_start_y + sub_height + GAP 
        
        # Subtitle Position (Centered)
        subtitle_x = (CANVAS_WIDTH - subtitle_width) // 2
        subtitle_y = block_start_y
        
        # 4. Rendering
        
        # Create Shadow Layer
        text_items = [
            (genre, title_font, (title_x, title_y), 0),
            (subtitle_text, subtitle_font, (subtitle_x, subtitle_y), subtitle_spacing)
        ]
        
        shadow_layer = create_soft_shadow(img.size, text_items, blur_radius=15)
        
        # Composite Shadow
        img = Image.alpha_composite(img, shadow_layer)
        
        # Draw Main Text
        main_draw = ImageDraw.Draw(img)
        
        # Draw Subtitle
        draw_text_with_spacing(main_draw, (subtitle_x, subtitle_y), subtitle_text, subtitle_font, spacing=subtitle_spacing, fill="white")
        
        # Draw Title
        draw_text_with_spacing(main_draw, (title_x, title_y), genre, title_font, spacing=0, fill="white")
        
        # Convert back to RGB and Save
        img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=95)
        logging.info(f"Thumbnail saved: {output_path}")
        return True

    except Exception as e:
        logging.error(f"Error generating thumbnail: {e}")
        import traceback
        traceback.print_exc()
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

    # Create a test cover image (blue gradient)
    test_cover = "/tmp/test_cover.png"
    img = Image.new('RGB', (1920, 1080), (30, 60, 90))
    draw = ImageDraw.Draw(img)
    # Add gradient effect
    for y in range(1080):
        color = (30 + y // 20, 60 + y // 20, 90 + y // 15)
        draw.line([(0, y), (1920, y)], fill=color)
    img.save(test_cover)

    # Generate thumbnail
    test_output = "/tmp/thumbnail.jpg"
    generate_thumbnail(test_idea_file, test_cover, test_output)

    os.unlink(test_idea_file)
    print(f"Test output: {test_output}")
