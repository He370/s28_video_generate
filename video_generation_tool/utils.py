from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def create_placeholder_image(text: str, output_path: str, size=(1280, 720), bg_color=(0, 0, 0), text_color=(255, 255, 255)):
    """
    Creates a placeholder image with text.
    """
    img = Image.new('RGB', size, color=bg_color)
    d = ImageDraw.Draw(img)
    
    # Try to load a default font, otherwise use default
    try:
        font = ImageFont.truetype("Arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    # Wrap text
    lines = textwrap.wrap(text, width=50)
    y_text = size[1] // 2 - (len(lines) * 25) # Approximate centering
    
    for line in lines:
        # Get text bbox to center it
        bbox = d.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) / 2
        d.text((x, y_text), line, font=font, fill=text_color)
        y_text += text_height + 10

    img.save(output_path)

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_image_with_retry(client, image_prompt, output_path, max_retries=3, max_times_gen_new_prompt=1, model=None, reference_image_path=None):
    """
    Tries to generate an image with retries.
    If generation fails, it can try to generate a new prompt using the Gemini client.
    """
    import time
    RETRY_DELAY = 1
    
    current_prompt = image_prompt
    
    for attempt in range(max_retries):
        try:
            client.generate_image(current_prompt, output_path, model=model, reference_image_path=reference_image_path)
            return True
        except Exception as e:
            print(f"  Error generating image (attempt {attempt+1}/{max_retries}): {e}")
            
            # If we have retries left and we are allowed to generate new prompts
            if attempt < max_retries - 1 and max_times_gen_new_prompt > 0:
                print("  Attempting to generate a new image prompt...")
                try:
                    # Ask Gemini to fix the prompt based on the error (if possible) or just simplify it
                    fix_prompt_request = f"""
                    The following image generation prompt failed with error: "{str(e)}".
                    
                    Original Prompt:
                    {current_prompt}
                    
                    Please rewrite this prompt to be more compatible with the image generation model. 
                    Keep the core visual description but simplify complex instructions or remove potentially problematic terms.
                    """
                    new_prompt = client.generate_text(fix_prompt_request)
                    print(f"  New prompt generated: {new_prompt[:100]}...")
                    current_prompt = new_prompt
                    max_times_gen_new_prompt -= 1
                except Exception as prompt_error:
                    print(f"  Failed to generate new prompt: {prompt_error}")
            
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                print(f"  Failed to generate image after {max_retries} attempts.")
                return False
    return False
