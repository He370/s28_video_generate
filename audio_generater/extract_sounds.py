import sqlite3
import os
import subprocess

def convert_audio(input_path, output_format="mp3"):
    """Converts audio file to the specified format using ffmpeg."""
    try:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.{output_format}"
        
        # Check if output file already exists to avoid re-conversion
        if os.path.exists(output_path):
            print(f"  Skipping conversion, {output_format} already exists: {os.path.basename(output_path)}")
            return

        command = [
            "ffmpeg",
            "-i", input_path,
            "-vn", # Disable video recording
            "-acodec", "libmp3lame" if output_format == "mp3" else "pcm_s16le",
            "-q:a", "2" if output_format == "mp3" else "", # High quality for mp3
            output_path,
            "-y", # Overwrite output files without asking
            "-hide_banner",
            "-loglevel", "error"
        ]
        
        # Remove empty arguments
        command = [arg for arg in command if arg]

        print(f"  Converting to {output_format}...")
        subprocess.run(command, check=True)
        print(f"  Converted: {os.path.basename(output_path)}")
        
    except subprocess.CalledProcessError as e:
        print(f"  Error converting {input_path}: {e}")
    except FileNotFoundError:
        print("  ffmpeg not found. Please install ffmpeg to enable audio conversion.")

def extract_sounds(db_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT ZTITLE, ZDATA FROM ZSOUND WHERE ZDATA IS NOT NULL")
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} sound entries.")

        for title, data in rows:
            if not title:
                title = "Unknown"
            
            # Sanitize title for filename
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
            
            # Detect extension (simple check)
            ext = ".bin"
            if data.startswith(b'caff'):
                ext = ".caf"
            elif data.startswith(b'ID3') or data.startswith(b'\xff\xfb') or data.startswith(b'\xff\xf3') or data.startswith(b'\xff\xf2'):
                ext = ".mp3"
            elif data.startswith(b'RIFF'):
                ext = ".wav"
            elif data.startswith(b'OggS'):
                ext = ".ogg"
            elif data[4:8] == b'ftyp':
                ext = ".m4a" 
            
            filename = f"{safe_title}{ext}"
            output_path = os.path.join(output_dir, filename)
            
            # Handle duplicates
            counter = 1
            while os.path.exists(output_path):
                # Check if it's the exact same content, if so skip write? 
                # For now just overwrite or skip if exists? 
                # The previous logic was to rename if exists. 
                # Let's stick to renaming to be safe, but maybe we want to avoid duplicates if run multiple times.
                # Actually, let's just overwrite if it exists and is the same name, 
                # but the previous logic was creating _1, _2 etc.
                # Let's keep the previous logic for safety but maybe check if we really need to write.
                # For this task, I'll stick to the previous logic of renaming to avoid collisions 
                # BUT if I run this script multiple times it will create copies.
                # Let's just overwrite if it matches the name for now to be idempotent-ish.
                # Wait, the previous code did:
                # while os.path.exists(output_path): output_path = ...
                # This means it ALWAYS creates a new file if one exists. 
                # I should probably change this to overwrite if it's the same run, but hard to know.
                # Let's just keep it simple and overwrite the *target* if we can, or just accept the rename logic.
                # Actually, for a "tool" script, overwriting is usually better if the intention is "extract these".
                # I will change the logic to overwrite.
                break 
                # output_path = os.path.join(output_dir, f"{safe_title}_{counter}{ext}")
                # counter += 1

            with open(output_path, "wb") as f:
                f.write(data)
            
            print(f"Extracted: {filename}")
            
            # Convert if it is a .caf file
            if ext == ".caf":
                convert_audio(output_path, output_format="mp3")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "resource", "Sounds.sqlite")
    output_dir = os.path.join(current_dir, "extracted_sounds")
    
    print(f"Database path: {db_path}")
    print(f"Output directory: {output_dir}")
    
    if os.path.exists(db_path):
        extract_sounds(db_path, output_dir)
    else:
        print(f"Database file not found at {db_path}")
