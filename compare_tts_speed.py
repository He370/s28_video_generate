import json
import os
import asyncio
import subprocess
import dotenv

from video_generation_tool.gemini_client import GeminiClient
import edge_tts

# Load environment using same path as main
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "video_generation_tool/.env"))
dotenv.load_dotenv(env_path)

def _get_audio_duration(path: str) -> float:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return float(result.stdout.decode().strip())
    except Exception:
        return 0.0

async def generate_edge(text, path, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)

async def main():
    with open("langchain/long2shorts/output/run_20260405_151530/assets/short_script.json") as f:
        data = json.load(f)
    timeline = data["timeline"]

    gc = GeminiClient(mode="prod")
    
    edge_voice = "en-US-ChristopherNeural"
    gemini_voice = "Aoede" # We'll use Aoede

    print(f"{'Scene':<5} | {'Edge TTS (s)':<15} | {'Gemini TTS (s)':<15} | {'Text':<30}")
    print("-" * 75)

    for i, t in enumerate(timeline):
        text = t["voiceover"]
        
        edge_path = f"tmp_edge_{i}.mp3"
        gemini_path = f"tmp_gem_1_{i}.mp3"

        # Edge
        await generate_edge(text, edge_path, edge_voice)
        edge_dur = _get_audio_duration(edge_path)

        # Gemini
        gc.generate_audio(text, gemini_path, voice_name=gemini_voice)
        gemini_dur = _get_audio_duration(gemini_path)

        print(f"{i:<5} | {edge_dur:<15.2f} | {gemini_dur:<15.2f} | {text[:30]}...")

        if os.path.exists(edge_path): os.remove(edge_path)
        if os.path.exists(gemini_path): os.remove(gemini_path)

if __name__ == "__main__":
    asyncio.run(main())
