import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure we can import from video_generation_tool
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from video_generation_tool.gemini_client import GeminiClient
from video_generation_tool.script_generator import ScriptGenerator

def main():
    try:
        print("Initializing Gemini Client...")
        client = GeminiClient(mode="dev") # Use dev mode to avoid delays if possible, though generate_text might still call API
        
        print("Initializing Script Generator...")
        generator = ScriptGenerator(client)
        
        context = "The history of the internet"
        language = "English"
        category = "History"
        word_limit = 200
        
        print(f"Generating script for: {context}")
        script = generator.generate_script(context, language, category, word_limit)
        
        print("\n--- Generated Script ---\n")
        print(script)
        print("\n------------------------\n")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
