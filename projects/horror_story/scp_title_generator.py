import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

def convert_svg_to_png(svg_path: str, png_path: str, width: int = 500):
    """
    Convert SVG to PNG using qlmanage (macOS QuickLook).
    Note: qlmanage produces a PNG with a specific width, usually good enough for thumbnails.
    It actually generates a file named with .png extension appended to the output path if we aren't careful,
    but we can rename it.
    """
    if os.path.exists(png_path):
        return True
    
    try:
        # qlmanage -t -s <width> -o <output_dir> <svg_file>
        # It generates <filename>.svg.png in the output dir
        output_dir = os.path.dirname(png_path)
        
        cmd = [
            "qlmanage", "-t", "-s", str(width), 
            "-o", output_dir, 
            svg_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # qlmanage appends .png to the original filename
        generated_file = os.path.join(output_dir, os.path.basename(svg_path) + ".png")
        
        if os.path.exists(generated_file):
            if os.path.exists(png_path):
                os.remove(png_path)
            
            # Post-process: Crop transparent areas to restore aspect ratio
            try:
                img = Image.open(generated_file).convert("RGBA")
                bbox = img.getbbox()
                if bbox:
                    cropped = img.crop(bbox)
                    cropped.save(png_path)
                else:
                    # Fallback if empty
                    os.rename(generated_file, png_path)
            except Exception as e:
                print(f"Error cropping converted PNG: {e}")
                # Fallback
                if os.path.exists(generated_file):
                     # Copy instead of rename if open failed but file exists
                     import shutil
                     shutil.move(generated_file, png_path)

            return True
        return False
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
        return False

def overlay_scp_title(base_image_path: str, title_text: str, output_path: str):
    """
    Overlay SCP Foundation logo and title on the base image.
    Style: Clinical, "Classified" dossier look.
    """
    try:
        project_dir = os.path.dirname(os.path.abspath(__file__))
        logo_svg = os.path.join(project_dir, "SCP_Foundation_logo.svg")
        logo_png = os.path.join(project_dir, "SCP_Foundation_logo.png")
        
        # Convert SVG to PNG if needed
        if not os.path.exists(logo_png):
            if os.path.exists(logo_svg):
                success = convert_svg_to_png(logo_svg, logo_png, width=1000)
                if not success:
                    print("Example warning: Could not convert SCP logo SVG to PNG.")
            else:
                print(f"Warning: SCP logo SVG not found at {logo_svg}")
        
        # Open Base Image
        img = Image.open(base_image_path).convert("RGBA")
        target_size = (1920, 1080)
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        width, height = target_size
        
        # Create Overlay Layer
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        if os.path.exists(logo_png):
            logo = Image.open(logo_png).convert("RGBA")
            
            # Make white background transparent
            datas = logo.getdata()
            new_data = []
            for item in datas:
                # Check for white-ish pixels (R, G, B > 200)
                if item[0] > 200 and item[1] > 200 and item[2] > 200:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            logo.putdata(new_data)

            # Resize logo relative to width (25%)
            logo_width = int(width * 0.25)
            aspect_ratio = logo.height / logo.width
            logo_height = int(logo_width * aspect_ratio)
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Position: Top Left with relative padding (1.5% of width)
            logo_x = int(width * 0.015)
            logo_y = int(width * 0.015)
            overlay.alpha_composite(logo, dest=(logo_x, logo_y))
        
        # 2. Add Title (Centered)
        # Style: "SCP-XXX" in large white text, centered
        
        # Fonts
        font_path = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"
        if not os.path.exists(font_path):
             font_path = "/System/Library/Fonts/Helvetica.ttc"
        
        # Parse Title to get "SCP-XXX" and "The Name"
        if ":" in title_text:
            parts = title_text.split(":", 1)
            scp_id = parts[0].strip().upper() # SCP-178
            scp_name = parts[1].strip()       # The 3D Specs
        else:
            scp_id = "SCP-UNKNOWN"
            scp_name = title_text
            
        # Draw SCP ID (Large - 20% of height)
        id_font_size = int(height * 0.20)
        try:
            id_font = ImageFont.truetype(font_path, id_font_size)
        except:
             id_font = ImageFont.load_default()
        
        # Draw SCP Name (Medium - 10% of height)
        name_font_size = int(height * 0.10)
        try:
            name_font = ImageFont.truetype(font_path, name_font_size)
        except:
            name_font = ImageFont.load_default()
            
        # Calculate Dimensions
        bbox_id = id_font.getbbox(scp_id)
        id_width = bbox_id[2] - bbox_id[0]
        id_height = bbox_id[3] - bbox_id[1]
        
        bbox_name = name_font.getbbox(scp_name)
        name_width = bbox_name[2] - bbox_name[0]
        name_height = bbox_name[3] - bbox_name[1]
        
        # Spacing
        gap = int(height * 0.03)
        total_content_height = id_height + gap + name_height
        
        # Center positions
        center_x = width // 2
        center_y = height // 2
        
        start_y = center_y - (total_content_height // 2)
        
        id_x = center_x - (id_width // 2)
        id_y = start_y
        
        name_x = center_x - (name_width // 2)
        name_y = id_y + id_height + gap
        
        # Text settings
        text_color = (255, 255, 255, 255)
        shadow_color = (0, 0, 0, 200)
        shadow_offset = int(height * 0.005)
        
        # Draw ID with Shadow
        draw.text((id_x + shadow_offset, id_y + shadow_offset), scp_id, font=id_font, fill=shadow_color)
        draw.text((id_x, id_y), scp_id, font=id_font, fill=text_color)
        
        # Draw Name with Shadow (No Background)
        draw.text((name_x + shadow_offset, name_y + shadow_offset), scp_name, font=name_font, fill=shadow_color)
        draw.text((name_x, name_y), scp_name, font=name_font, fill=text_color)
        
        # Composite
        final_img = Image.alpha_composite(img, overlay)
        final_img = final_img.convert("RGB")
        
        final_img.save(output_path, "PNG")
        print(f"Generated SCP title image at {output_path}")
        return True
        
    except Exception as e:
        print(f"Error overlaying SCP title: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test block
if __name__ == "__main__":
    # Create dummy base image
    dummy_path = "/tmp/scp_test_base.png"
    Image.new("RGB", (1920, 1080), (50, 50, 50)).save(dummy_path)
    
    overlay_scp_title(dummy_path, "SCP-178: The 3D Specs", "/tmp/scp_test_result.png")

def create_thumbnail(source_path: str, thumbnail_path: str, max_size_bytes: int = 2000000):
    """
    Create a thumbnail from the source image that fits within the max_size_bytes.
    Converts to JPEG and adjusting quality/size if needed.
    """
    try:
        img = Image.open(source_path).convert("RGB")
        
        # Start with high quality
        quality = 95
        
        while True:
            img.save(thumbnail_path, "JPEG", quality=quality)
            
            file_size = os.path.getsize(thumbnail_path)
            if file_size < max_size_bytes:
                print(f"Created thumbnail at {thumbnail_path} ({file_size/1024:.1f} KB)")
                return True
            
            # Reduce quality
            quality -= 5
            if quality < 30:
                # If quality gets too low, start resizing
                print(f"Quality low ({quality}), resizing image...")
                width, height = img.size
                img = img.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
                quality = 80 # Reset quality for resized image
            
            if quality < 10 and img.size[0] < 300:
                print("Could not reduce file size enough.")
                return False
                
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return False

