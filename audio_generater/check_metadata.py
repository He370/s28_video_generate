import os
import sys
import subprocess

def check_metadata_ffprobe(file_path):
    """Checks metadata using ffprobe (requires ffmpeg installed)."""
    print(f"--- Metadata for {os.path.basename(file_path)} (via ffprobe) ---")
    try:
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            file_path
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            tags = data.get("format", {}).get("tags", {})
            if tags:
                for k, v in tags.items():
                    print(f"{k}: {v}")
            else:
                print("No tags found in format section.")
        else:
            print("Error running ffprobe.")
    except FileNotFoundError:
        print("ffprobe not found. Please install ffmpeg.")
    print("-" * 30)

def check_metadata_mutagen(file_path):
    """Checks metadata using mutagen (requires pip install mutagen)."""
    print(f"--- Metadata for {os.path.basename(file_path)} (via mutagen) ---")
    try:
        import mutagen
        from mutagen.mp3 import MP3
        from mutagen.easyid3 import EasyID3
        from mutagen.id3 import ID3
        
        f = mutagen.File(file_path)
        if f is None:
            print("Mutagen could not parse the file.")
            return

        # Print all found tags
        print("Raw Tags:")
        for key, value in f.tags.items() if f.tags else []:
            print(f"  {key}: {value}")
            
        # Specific check for Copyright
        # ID3v2 frame for copyright is 'TCOP'
        if isinstance(f.tags, ID3):
            copyright_info = f.tags.get("TCOP")
            if copyright_info:
                print(f"\nCopyright (TCOP): {copyright_info}")
            else:
                print("\nNo 'TCOP' (Copyright) frame found.")
                
    except ImportError:
        print("mutagen library not found. Run 'pip install mutagen' to use this method.")
    except Exception as e:
        print(f"Error reading metadata: {e}")
    print("-" * 30)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_metadata.py <path_to_audio_file>")
        # Default to checking one of the extracted files if no arg provided
        default_file = os.path.join(os.path.dirname(__file__), "extracted_sounds", "Clock.mp3")
        if os.path.exists(default_file):
            print(f"No file provided, checking default: {default_file}")
            check_metadata_ffprobe(default_file)
            check_metadata_mutagen(default_file)
    else:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            check_metadata_ffprobe(file_path)
            check_metadata_mutagen(file_path)
        else:
            print(f"File not found: {file_path}")
