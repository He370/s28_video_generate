from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv("video_generation_tool/.env")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

model_name = "gemini-2.5-flash-image"
print(f"Testing {model_name} with generate_images...")

try:
    response = client.models.generate_images(
        model=model_name,
        prompt="A simple test image of a cat",
        config=types.GenerateImagesConfig(number_of_images=1)
    )
    print("Success!")
    if response.generated_images:
        print("Image generated.")
    else:
        print("No image returned.")
except Exception as e:
    print(f"Error: {e}")
