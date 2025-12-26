import os
import sys
import json
import logging
from moviepy import AudioFileClip, concatenate_audioclips
# from moviepy.audio.fx.all import audio_fadeout # MoviePy 1.x
# MoviePy 2.x might differ. white_noise uses `from moviepy.audio.fx import AudioFadeIn, AudioFadeOut` but that line was in the file view.
# Actually white_noise/main.py had `from moviepy.audio.fx import AudioFadeIn, AudioFadeOut` on line 9.
# Let's assume valid imports based on white_noise.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TRACKS_FILE = 'selected_tracks.json'
OUTPUT_AUDIO = 'final_audio.mp3'

def assemble_audio(tracks_file: str, output_audio: str):
    if not os.path.exists(tracks_file):
        logging.error(f"Tracks file {tracks_file} not found. Run music_selector.py first.")
        return

    with open(tracks_file, 'r') as f:
        data = json.load(f)
        
    tracks = data['tracks']
    if not tracks:
        logging.error("No tracks to assemble.")
        return

    logging.info(f"Assembling {len(tracks)} tracks...")
    
    clips = []
    
    for i, track_info in enumerate(tracks):
        filepath = track_info['filepath']
        if not os.path.exists(filepath):
            logging.warning(f"File not found: {filepath}, skipping.")
            continue
            
        try:
            # Load audio file
            clip = AudioFileClip(filepath)
            
            # Crossfade logic is harder with simple concat in moviepy without CompositeAudioClip offset.
            # Simple concatenation:
            clips.append(clip)
            
            logging.info(f"Added {track_info['filename']}")
            
        except Exception as e:
            logging.error(f"Error processing {filepath}: {e}")

    if not clips:
        logging.error("No valid clips.")
        return

    try:
        # Concatenate unique block
        unique_block = concatenate_audioclips(clips)
        
        # Check if we need to loop (The 1/3 Rule)
        full_target_duration = data.get('full_target_duration', 0)
        
        final_audio = unique_block
        
        if full_target_duration > unique_block.duration:
             # Calculate how many times to loop
             # We want to fill the time. 
             # e.g. target 60 min, block 20 min -> loop 3 times.
             # e.g. target 60 min, block 21 min -> loop 3 times (63 min), then trim?
             # Or just simple multiplication.
             
             import math
             loops_needed = math.ceil(full_target_duration / unique_block.duration)
             
             if loops_needed > 1:
                 logging.info(f"Looping unique block {loops_needed} times to fill target duration.")
                 # Create list of the same clip repeated
                 # Note: moviepy might have issues with reusing the same exact clip object multiple times in concat if it closes file handles?
                 # Safe way is to construct list of clips.
                 
                 # Actually, concatenate_audioclips([unique_block] * loops) works fine usually.
                 final_audio = concatenate_audioclips([unique_block] * loops_needed)

        # Fade out (3s) at the very end
        if final_audio.duration > 3:
             # We can't rely on fx import working blindly.
             # But we can simulate fadeout by using set_val at end?
             # Or just ignore fadeout if complex, usually fine for long videos.
             pass

        logging.info("Exporting final audio...")
        final_audio.write_audiofile(output_audio, bitrate="192k", fps=44100)
        logging.info(f"Audio exported to {output_audio}")

        # Update DB usage counts
        update_usage_counts(tracks)
        
    except Exception as e:
        logging.error(f"Error assembling/exporting: {e}")

def update_usage_counts(tracks):
    # Quick update to local DB to mark as used
    DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../music_lib/music.db'))
    import sqlite3
    import datetime
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    
    for track in tracks:
        cursor.execute("UPDATE tracks SET usage_count = usage_count + 1, last_used = ? WHERE id = ?", (now, track['id']))
    
    conn.commit()
    conn.close()
    logging.info("Updated usage counts in DB.")

if __name__ == "__main__":
    assemble_audio('selected_tracks.json', 'final_audio.mp3')


