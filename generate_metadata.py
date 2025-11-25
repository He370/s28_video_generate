import argparse
import os
import sys
from dotenv import load_dotenv
from video_generation_tool.gemini_client import GeminiClient

# Load environment variables
load_dotenv()

# Usage: python3 generate_metadata.py projects/today_history/output/video_5/assets/script.txt

def generate_video_metadata(script_path: str):
    """
    Generates a YouTube video title and description based on the script content.
    """
    if not os.path.exists(script_path):
        print(f"Error: Script file not found at {script_path}")
        return

    with open(script_path, "r") as f:
        script_content = f.read()

    client = GeminiClient(mode="prod")

    system_prompt = f"""
    You are an expert YouTube strategist and copywriter.
    Your task is to create a high-performing YouTube video title and description based on the provided video script.
    
    Script:
    {script_content}
    
    Please provide the output in the following format:
    
    TITLE:
    [Insert 3 catchy, click-worthy title options here]
    
    DESCRIPTION:
    [Insert a SEO-optimized video description here. Include a hook in the first couple of lines, a summary of the content, and relevant hashtags at the end.]
    """

    print("Analyzing script and generating metadata...")
    try:
        metadata = client.generate_text(system_prompt)
        print("\n--- Generated Video Metadata ---\n")
        print(metadata)
        print("\n--------------------------------\n")
    except Exception as e:
        print(f"Error generating metadata: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate YouTube title and description from a script file.")
    parser.add_argument("script_path", help="Path to the script.txt file")
    
    args = parser.parse_args()
    
    generate_video_metadata(args.script_path)
