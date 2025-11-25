import argparse
import os
import sys
from dotenv import load_dotenv
from video_generation_tool.gemini_client import GeminiClient

# Load environment variables
load_dotenv()

# USAGE: python3 generate_cover_prompt.py projects/today_history/output/video_5/assets/script.txt


def generate_cover_prompt(script_path: str, style: str = "cinematic, photorealistic, high contrast, 8k"):
    """
    Generates an attractive video cover image prompt based on the script content.
    """
    if not os.path.exists(script_path):
        print(f"Error: Script file not found at {script_path}")
        return

    with open(script_path, "r") as f:
        script_content = f.read()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return

    client = GeminiClient(mode="prod")

    system_prompt = f"""
    You are an expert visual designer and AI image prompt engineer.
    Your task is to create a highly attractive, click-worthy video cover (thumbnail) image prompt based on the provided video script.
    
    The image prompt should:
    1.  Capture the most exciting, dramatic, or intriguing element of the script.
    2.  Be visually striking with high contrast and vibrant or dramatic lighting.
    3.  Be suitable for a YouTube thumbnail or video cover.
    4.  Include technical keywords for high quality (e.g., 8k, photorealistic, cinematic lighting).
    5.  NOT include any text instructions for the image generation model (unless it's for a sign or label within the scene, but generally avoid text).
    
    Script:
    {script_content}
    
    Desired Style: {style}
    
    Output ONLY the image prompt.
    """

    print("Analyzing script and generating cover prompt...")
    try:
        cover_prompt = client.generate_text(system_prompt)
        print("\n--- Generated Cover Image Prompt ---\n")
        print(cover_prompt)
        print("\n------------------------------------\n")
    except Exception as e:
        print(f"Error generating prompt: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video cover image prompt from a script file.")
    parser.add_argument("script_path", help="Path to the script.txt file")
    parser.add_argument("--style", default="cinematic, photorealistic, high contrast, 8k", help="Desired image style")
    
    args = parser.parse_args()
    
    generate_cover_prompt(args.script_path, args.style)
