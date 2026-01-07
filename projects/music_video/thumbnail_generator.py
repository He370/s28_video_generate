import os
import sys
import json
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_thumbnail(idea_file: str, cover_image: str, output_path: str):
    """
    Generate a YouTube thumbnail using the cover image and title text.
    
    The thumbnail will:
    - Use the cover image as background
    - Overlay title and description text
    - Match the style from the reference image (bold white text)
    - Export at 1280x720 (YouTube recommended resolution)
    
    Args:
        idea_file: Path to idea.json containing title and description
        cover_image: Path to cover image (background)
        output_path: Path to save thumbnail (should be 'thumbnail.jpg')
    """
    if not os.path.exists(idea_file):
        logging.error(f"Idea file {idea_file} not found.")
        return False
        
    if not os.path.exists(cover_image):
        logging.error(f"Cover image {cover_image} not found.")
        return False
    
    with open(idea_file, 'r') as f:
        idea = json.load(f)
    
    genre = idea.get('genre', 'Music')
    
    logging.info(f"Generating thumbnail for genre: '{genre}'")
    
    try:
        # Open and resize cover image to 1280x720
        img = Image.open(cover_image)
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # Optional: Add a subtle dark overlay to make text more readable
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 80))
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Load font for genre
        try:
            # Use modern font for genre
            genre_font = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", 80)
        except:
            try:
                genre_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 80)
            except:
                genre_font = ImageFont.load_default()
        
        # Get genre text bounding box
        genre_text = genre.upper()
        genre_bbox = draw.textbbox((0, 0), genre_text, font=genre_font)
        genre_width = genre_bbox[2] - genre_bbox[0]
        genre_height = genre_bbox[3] - genre_bbox[1]
        
        # Center both horizontally and vertically
        genre_x = (1280 - genre_width) // 2
        genre_y = (720 - genre_height) // 2
        
        # Draw shadow
        shadow_offset = 4
        draw.text((genre_x + shadow_offset, genre_y + shadow_offset), genre_text, 
                 font=genre_font, fill=(0, 0, 0, 200))
        
        # Draw main text
        draw.text((genre_x, genre_y), genre_text, font=genre_font, fill=(255, 255, 255, 255))
        
        # Save as JPEG (YouTube standard)
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
        "genre": "Ambient"
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
