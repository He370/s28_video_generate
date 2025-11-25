from google import genai
import os
from dotenv import load_dotenv

load_dotenv("video_generation_tool/.env")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("Listing models...")
try:
    for model in client.models.list():
        if "image" in model.name or "imagen" in model.name:
            print(f"Found image model: {model.name}")
        else:
            # print(f"Found model: {model.name}") # Commented out to reduce noise
            pass
except Exception as e:
    print(f"Error listing models: {e}")
