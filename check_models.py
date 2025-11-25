import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("video_generation_tool/.env")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def test_model(model_name):
    print(f"Testing {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        if hasattr(model, 'generate_images'):
            print(f"  {model_name} has generate_images")
        else:
            print(f"  {model_name} DOES NOT have generate_images")
            
        # Check if it supports generateContent
        try:
            response = model.generate_content("Test")
            print(f"  {model_name} generate_content success")
        except Exception as e:
            print(f"  {model_name} generate_content failed: {e}")
            
    except Exception as e:
        print(f"  Failed to instantiate {model_name}: {e}")

def test_image_gen_model(model_name):
    print(f"Testing ImageGenerationModel with {model_name}...")
    try:
        if hasattr(genai, 'ImageGenerationModel'):
            model = genai.ImageGenerationModel(model_name)
            if hasattr(model, 'generate_images'):
                print(f"  {model_name} via ImageGenerationModel has generate_images")
            else:
                print(f"  {model_name} via ImageGenerationModel DOES NOT have generate_images")
        else:
            print("  genai.ImageGenerationModel does not exist")
    except Exception as e:
        print(f"  Failed to instantiate ImageGenerationModel {model_name}: {e}")

print("--- Checking Models ---")
# test_model("gemini-2.5-flash-image") # Skip to avoid quota
test_image_gen_model("imagen-3.0-generate-001")
test_image_gen_model("gemini-2.5-flash-image")
