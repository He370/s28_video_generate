import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

class GeminiClient:
    def __init__(self, mode: str = "dev"):
        self.mode = mode
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        from .constants import GEMINI_TEXT_MODEL, GEMINI_IMAGE_MODEL, API_DELAY_SECONDS
        # self.image_model = genai.GenerativeModel(GEMINI_IMAGE_MODEL) # Old SDK
        self.client = genai.Client(api_key=api_key) # New SDK Client
        
        if self.mode == "dev":
            self.delay = 0
        else:
            self.delay = API_DELAY_SECONDS

    def generate_image_prompt(self, text: str) -> str:
        """
        Generates a detailed image prompt based on the event text.
        """
        from .constants import IMAGE_STYLE_PROMPT, GEMINI_TEXT_MODEL
        prompt = f"""
        Create a detailed image generation prompt for the following historical event or fact. 
        {IMAGE_STYLE_PROMPT}
        
        Event: {text}
        
        Output only the prompt text.
        """
        try:
            time.sleep(self.delay)
            response = self.client.models.generate_content(model=GEMINI_TEXT_MODEL, contents=prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return text

    # Note: Actual image generation with Gemini API (Imagen) might require specific client setup 
    # or might not be fully available in the standard `google-generativeai` package depending on the version/access.
    # For now, I will implement a placeholder that saves a dummy image or uses a public placeholder if API fails.
    # In a real scenario with access, we would use the appropriate method.
    
    def generate_image(self, prompt: str, output_path: str, model: Optional[str] = None, reference_image_path: Optional[str] = None):
        """
        Generates an image using Gemini/Imagen (via new google-genai SDK).
        Supports both Imagen (generate_images) and Gemini (generate_content) models.
        """
        if self.mode == "dev":
            print(f"DEV MODE: Generating dummy image for prompt: {prompt}")
            if reference_image_path:
                print(f"DEV MODE: Using reference image: {reference_image_path}")
            try:
                # Create a dummy image with text
                width, height = 1920, 1080
                img = Image.new('RGB', (width, height), color=(73, 109, 137))
                d = ImageDraw.Draw(img)
                
                # Try to load a font, fallback to default if not available
                try:
                    font = ImageFont.truetype("Arial.ttf", 40)
                except IOError:
                    font = ImageFont.load_default()
                
                # Wrap text
                import textwrap
                lines = textwrap.wrap(prompt, width=60)
                y_text = height // 2 - (len(lines) * 25)
                
                for line in lines:
                    bbox = d.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    d.text(((width - text_width) / 2, y_text), line, font=font, fill=(255, 255, 0))
                    y_text += text_height + 10
                
                img.save(output_path)
                print(f"Dummy image saved to {output_path}")
                return
            except Exception as e:
                print(f"Error generating dummy image: {e}")
                # Fallback to creating a simple colored square if PIL fails completely
                with open(output_path, "wb") as f:
                    f.write(b'\x00' * 1024) # Write some garbage
                return

        from .constants import GEMINI_IMAGE_MODEL
        
        # Use provided model or default from constants
        target_model = model if model else GEMINI_IMAGE_MODEL
        
        print(f"Generating image for prompt: {prompt}")
        
        try:
            time.sleep(self.delay)
            
            # Determine method based on model name or try/except
            # Imagen models usually use generate_images
            # Gemini models usually use generate_content
            
            if "imagen" in target_model.lower():
                try:
                    print(f"Attempting generate_images with {target_model}...")
                    response = self.client.models.generate_images(
                        model=target_model,
                        prompt=prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio="16:9",
                        )
                    )
                    if response.generated_images:
                        image_bytes = response.generated_images[0].image.image_bytes
                        with open(output_path, "wb") as f:
                            f.write(image_bytes)
                        print(f"Image saved to {output_path}")
                        return
                except Exception as e:
                    print(f"generate_images failed: {e}")
                    # If it was an Imagen model and failed (e.g. billing), we might stop here 
                    # unless we want to fallback to a different model, but here we just try the other method if applicable.
                    if "404" in str(e) or "400" in str(e):
                         # If it's a 404/400, maybe it's not an Imagen model or not available. 
                         # But if the user selected Imagen, we should probably raise or let it fall through to placeholder.
                         pass

            # Fallback or default for Gemini models: generate_content
            print(f"Attempting generate_content with {target_model}...")
            
            contents = [prompt]
            if reference_image_path and os.path.exists(reference_image_path):
                print(f"Using reference image: {reference_image_path}")
                try:
                    # Load reference image using PIL
                    ref_img = Image.open(reference_image_path)
                    contents.append(ref_img)
                except Exception as e:
                    print(f"Failed to load reference image: {e}")
            
            response = self.client.models.generate_content(
                model=target_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio="16:9",
                    )
                )
            )
            
            image_saved = False
            # Check for new SDK structure
            if hasattr(response, 'candidates') and response.candidates:
                parts = response.candidates[0].content.parts
            elif hasattr(response, 'parts'):
                parts = response.parts
            else:
                parts = []

            if parts:
                for part in parts:
                    if hasattr(part, "inline_data") and part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        with open(output_path, "wb") as f:
                            f.write(part.inline_data.data)
                        print(f"Image saved to {output_path}")
                        image_saved = True
                        break
            
            if not image_saved:
                print(f"No image found in response: {response.text if hasattr(response, 'text') else 'No text'}")
                raise ValueError("No image returned in response")
                
        except Exception as e:
            print(f"Error generating image: {e}")
            raise e

    def generate_text(self, prompt: str, response_mime_type: str = "text/plain", model: Optional[str] = None) -> str:
        """
        Generates text content using Gemini.
        """
        from .constants import GEMINI_TEXT_MODEL

        target_model = model if model else GEMINI_TEXT_MODEL

        try:
            time.sleep(self.delay)
            config = types.GenerateContentConfig(response_mime_type=response_mime_type)
            response = self.client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"Error generating text: {e}")
            return ""

    def generate_video(self, prompt: str, output_path: str, model: Optional[str] = None, image_path: Optional[str] = None) -> None:
        """
        Generates a video using Gemini (Veo).
        """
        from .constants import GEMINI_VIDEO_MODEL
        target_model = model if model else GEMINI_VIDEO_MODEL

        print(f"Generating video with model: {target_model}")
        print(f"Prompt: {prompt}")

        if self.mode == "dev":
            print(f"DEV MODE: Generating dummy video for prompt: {prompt}")
            import subprocess
            try:
                 # Create a dummy image first
                 dummy_img = "dummy_frame.png"
                 Image.new('RGB', (1280, 720), color = 'red').save(dummy_img)
                 subprocess.run([
                     "ffmpeg", "-y", "-loop", "1", "-i", dummy_img, "-c:v", "libx264", "-t", "4", "-pix_fmt", "yuv420p", output_path
                 ], check=True)
                 os.remove(dummy_img)
                 print(f"Dummy video created at {output_path}")
                 return
            except Exception as ffmpeg_e:
                print(f"Failed to create dummy video: {ffmpeg_e}")
                return

        try:
            time.sleep(self.delay)
            
            # Load reference image using types.Image for proper encoding
            if image_path and os.path.exists(image_path):
                print(f"Using reference image: {image_path}")
                reference_image = types.Image.from_file(location=image_path)
            else:
                raise ValueError("Image path is required for Veo video generation")
            
            print(f"Calling client.models.generate_videos with {target_model}...")
            
            # Generate video from reference image
            operation = self.client.models.generate_videos(
                model=target_model,
                prompt=prompt,
                image=reference_image,
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                    duration_seconds=8,
                ),
            )
            
            # Poll the operation status until the video is ready
            max_wait_time = 600  # 10 minutes
            poll_interval = 10  # 10 seconds
            elapsed = 0
            
            while not operation.done:
                print(f"Waiting for video generation to complete... ({elapsed}s elapsed)")
                time.sleep(poll_interval)
                elapsed += poll_interval
                operation = self.client.operations.get(operation)
                
                if elapsed >= max_wait_time:
                    raise TimeoutError("Video generation timed out after 10 minutes")
            
            print("Video generation completed!")
            
            # Download the video
            video = operation.response.generated_videos[0]
            self.client.files.download(file=video.video)
            video.video.save(output_path)
            print(f"Video saved to {output_path}")

        except Exception as e:
            print(f"Error generating video: {e}")
            raise e

    def generate_seamless_loop_video(self, video_prompt: str, image_prompt: str, output_video_path: str, output_image_path: str, model_video: Optional[str] = None, model_image: Optional[str] = None) -> None:
        """
        Generates a seamless looping video by:
        1. Generating an image directly using models.generate_images.
        2. Using that image as both first/last frame for models.generate_videos.
        3. Saving both outputs.
        """
        from .constants import GEMINI_VIDEO_MODEL, GEMINI_IMAGE_MODEL
        
        target_model_image = model_image if model_image else GEMINI_IMAGE_MODEL
        target_model_video = model_video if model_video else GEMINI_VIDEO_MODEL
        
        print("Starting seamless loop video generation (Google Docs Pattern)...")

        try:
            time.sleep(self.delay)
            
            # 1. Generate Image
            print(f"Step 1: Generating image with {target_model_image}...")
            image_response = self.client.models.generate_images(
                model=target_model_image,
                prompt=image_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                )
            )
            
            if not image_response.generated_images:
                raise ValueError("No images generated")
                
            generated_image_obj = image_response.generated_images[0]
            image_file = generated_image_obj.image
            
            # Save the image
            with open(output_image_path, "wb") as f:
                f.write(image_file.image_bytes)
            print(f"Base image saved to {output_image_path}")

            # 2. Generate Video
            print(f"Step 2: Generating video with {target_model_video} using generated image as first/last frame...")
            
            video_operation = self.client.models.generate_videos(
                model=target_model_video,
                prompt=video_prompt,
                image=image_file,      # Use the image object directly
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                    duration_seconds=8,
                    last_frame=image_file  # Use the image object directly
                ),
            )
            
            # Poll for completion
            max_wait_time = 600  # 10 minutes
            poll_interval = 10
            elapsed = 0
            
            while not video_operation.done:
                print(f"Waiting for seamless video generation... ({elapsed}s elapsed)")
                time.sleep(poll_interval)
                elapsed += poll_interval
                video_operation = self.client.operations.get(video_operation)
                
                if elapsed >= max_wait_time:
                    raise TimeoutError("Video generation timed out")
            
            print("Video generation completed!")
            
            # Download and save video
            video_result = video_operation.response.generated_videos[0]
            self.client.files.download(file=video_result.video)
            video_result.video.save(output_video_path)
            print(f"Seamless video saved to {output_video_path}")

        except Exception as e:
            print(f"Error in seamless loop generation: {e}")
            raise e
