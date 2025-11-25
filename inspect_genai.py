import google.generativeai as genai
import inspect

print("genai version:", genai.__version__)
print("dir(genai):", dir(genai))

# Check for anything looking like image generation
for name in dir(genai):
    if "image" in name.lower():
        print(f"Found: {name}")
