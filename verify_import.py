import google.generativeai as old_genai
from google import genai as new_genai

print("Old SDK version:", old_genai.__version__)
# New SDK doesn't always have __version__ at top level easily, but let's check client
client = new_genai.Client(api_key="TEST")
print("New Client created:", client)
