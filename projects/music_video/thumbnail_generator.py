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
    
    title = idea.get('title', 'RELAX & FOCUS')
    genre = idea.get('genre', 'Music')
    
    logging.info(f"Generating thumbnail for: '{title}'")
    
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
        
        # Try to use Arial Bold for title, fallback to default
        try:
            # macOS system fonts
            title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 80)
            desc_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 36)
        except:
            try:
                # Linux fallback
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
                desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            except:
                logging.warning("Could not load custom fonts, using default")
                title_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()
        
        # Calculate text positions (centered)
        # Get text bounding boxes
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        
        genre_bbox = draw.textbbox((0, 0), genre.upper(), font=desc_font)
        genre_width = genre_bbox[2] - genre_bbox[0]
        genre_height = genre_bbox[3] - genre_bbox[1]
        
        # Center horizontally, position vertically in center
        title_x = (1280 - title_width) // 2
        title_y = (720 - title_height) // 2 - 40
        
        genre_x = (1280 - genre_width) // 2
        genre_y = title_y + title_height + 20
        
        # Draw text with shadow for better visibility
        # Shadow (black, offset)
        shadow_offset = 3
        draw.text((title_x + shadow_offset, title_y + shadow_offset), title, 
                 font=title_font, fill=(0, 0, 0, 200))
        draw.text((genre_x + shadow_offset, genre_y + shadow_offset), genre.upper(), 
                 font=desc_font, fill=(0, 0, 0, 200))
        
        # Main text (white)
        draw.text((title_x, title_y), title, font=title_font, fill=(255, 255, 255, 255))
        draw.text((genre_x, genre_y), genre.upper(), font=desc_font, fill=(255, 255, 255, 255))
        
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
