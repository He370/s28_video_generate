import sqlite3
import os
import glob
import datetime
import re
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

# Configuration
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'music.db')
ASSETS_DIR = os.path.join(BASE_DIR, 'music', 'assets')

def setup_db(db_path):
    """Creates the tracks table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            filepath TEXT,
            genre TEXT,
            mood TEXT,
            bpm INTEGER,
            duration INTEGER,
            date_added TIMESTAMP,
            last_used TIMESTAMP,
            usage_count INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    return conn

def extract_metadata_from_file(filepath):
    """Extracts metadata from MP3 ID3 tags."""
    try:
        audio = MP3(filepath, ID3=ID3)
        tags = audio.tags
        
        # Duration
        duration = int(audio.info.length)
        
        # Title
        title = str(tags.get('TIT2', os.path.splitext(os.path.basename(filepath))[0]))
        
        # Artist
        artist = str(tags.get('TPE1', 'Unknown Artist'))
        
        # Genre
        genre_frame = tags.get('TCON')
        genre = str(genre_frame) if genre_frame else 'Unknown'
        # Clean up genre (replace ; with ,)
        genre = genre.replace(';', ',')
        
        # BPM
        bpm_frame = tags.get('TBPM')
        try:
             bpm = int(str(bpm_frame)) if bpm_frame else 0
        except:
             bpm = 0
             
        # Mood (TXXX:mood)
        mood = 'Unknown'
        for key in tags.keys():
            if key.startswith('TXXX') and 'mood' in key.lower():
                 mood = str(tags[key])
                 break
        # Clean up mood
        mood = mood.replace(';', ',')

        return {
            'title': title,
            'artist': artist,
            'duration': duration,
            'bpm': bpm,
            'genre': genre,
            'mood': mood
        }
    except Exception as e:
        print(f"Error reading tags from {filepath}: {e}")
        return None

def parse_filename_fallback(filename):
    """Last resort fallback: Extrapolate metadata from filename."""
    clean_name = filename.replace('ES_', '', 1) if filename.startswith('ES_') else filename
    clean_name = os.path.splitext(clean_name)[0]
    
    title = clean_name
    artist = "Unknown Artist"
    
    if ' - ' in clean_name:
        parts = clean_name.split(' - ')
        title = parts[0]
        if len(parts) > 1:
            artist = parts[1]
            
    return {
        'title': title,
        'artist': artist,
        'duration': 0,
        'bpm': 0,
        'genre': 'Unknown',
        'mood': 'Unknown',
    }

def ingest_files(assets_dir, conn):
    """Scans files and ingests them into DB using file tags or fallback."""
    if not os.path.exists(assets_dir):
        print(f"Error: {assets_dir} not found.")
        return

    cursor = conn.cursor()
    files = glob.glob(os.path.join(assets_dir, '*.mp3'))
    
    print(f"Found {len(files)} files in {assets_dir}")

    now = datetime.datetime.now()

    for filepath in files:
        filename = os.path.basename(filepath)
        
        # Check if already exists
        cursor.execute("SELECT id FROM tracks WHERE filename = ?", (filename,))
        if cursor.fetchone():
            continue

        source = ""
        final_meta = {}

        # 1. Try to read from file tags
        file_meta = extract_metadata_from_file(filepath)
        if file_meta:
            final_meta = file_meta
            source = "File Tags"
        else:
            # 2. Fallback to filename
            final_meta = parse_filename_fallback(filename)
            source = "Filename Fallback"

        try:
            cursor.execute("""
                INSERT INTO tracks (filename, filepath, genre, mood, bpm, duration, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                filename,
                os.path.abspath(filepath),
                final_meta['genre'],
                final_meta['mood'],
                final_meta['bpm'],
                final_meta['duration'],
                now
            ))
            conn.commit()
            print(f"Added: {filename} (Source: {source} - Title: {final_meta['title']})")
        except Exception as e:
            print(f"Error inserting {filename}: {e}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Creating database at {DB_PATH}")
    
    conn = setup_db(DB_PATH)
    
    print("Ingesting files...")
    ingest_files(ASSETS_DIR, conn)
    
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
