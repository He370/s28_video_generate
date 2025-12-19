import argparse
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool.audio_generator import AudioGenerator

def main():
    parser = argparse.ArgumentParser(description="Test TTS prompt and settings.")
    parser.add_argument("--prompt", type=str, help="TTS Prompt prefix")
    parser.add_argument("--text", type=str, help="Text to speak")
    parser.add_argument("--voice", type=str, default="Charon", help="Voice name (default: Charon)")
    parser.add_argument("--output", type=str, default="test_tts.wav", help="Output file path")
    parser.add_argument("--mode", type=str, default="prod", choices=["prod", "dev"], help="Mode (prod/dev)")
    
    args = parser.parse_args()
    
    # Default horror prompt if not provided (matching current main.py)
    default_prompt = "Please read the following text in an eerie voice. Read at a normal, engaging pace: "
    prompt_prefix = args.prompt if args.prompt else default_prompt
    
    # Default text if not provided
    default_text = "The shadows lengthened across the floor, stretching like skeletal fingers reaching for my ankles. I held my breath, listening to the silence that was suddenly broken by a soft, wet scratching sound from inside the walls."
    text = args.text if args.text else default_text
    
    print(f"Testing TTS...")
    print(f"Voice: {args.voice}")
    print(f"Mode: {args.mode}")
    print(f"Prompt Prefix: '{prompt_prefix}'")
    print(f"Text: '{text}'")
    print(f"Output: {args.output}")
    
    try:
        audio_gen = AudioGenerator(
            language="English",
            mode=args.mode,
            voice_name=args.voice,
            prompt_prefix=prompt_prefix
        )
        
        audio_gen.generate_audio_sync(text, args.output)
        print(f"Success! Audio saved to {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
