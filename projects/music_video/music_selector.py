import os
import sys
import sqlite3
import json
import logging
import random
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../music_lib/music.db'))
IDEA_FILE = 'idea.json'
OUTPUT_FILE = 'selected_tracks.json'

def get_db_connection():
    return sqlite3.connect(DB_PATH)


def select_music(idea_file: str, output_file: str, duration_hours: int = 1):
    if not os.path.exists(idea_file):
        logging.error(f"Idea file {idea_file} not found. Run idea_generator.py first.")
        return

    with open(idea_file, 'r') as f:
        idea = json.load(f)
    
    target_genre = idea.get('genre', 'Ambient')
    bpm_range = idea.get('bpm_range', '60-90')
    
    # Parse BPM range
    try:
        min_bpm, max_bpm = map(int, str(bpm_range).split('-'))
    except:
        min_bpm, max_bpm = 0, 999
        logging.warning(f"Could not parse BPM range '{bpm_range}', using default.")

    logging.info(f"Selecting music: Genre={target_genre}, BPM={min_bpm}-{max_bpm}, Duration={duration_hours}h")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Strategy:
    # 1. Fetch all tracks of the target genre.
    # 2. Calculate a score for each track:
    #    - Base Score: 100
    #    - Usage Penalty: -10 * usage_count
    #    - BPM Bonus: +20 if within range, +10 if close (+/- 10), -10 if far
    #    - Date Bonus: +5 for recent (simple approximation or random tie-break)
    # 3. Sort by Score DESC
    
    query = """
        SELECT id, filename, filepath, duration, bpm, usage_count
        FROM tracks 
        WHERE genre LIKE ?
    """
    
    cursor.execute(query, (f"%{target_genre}%",))
    candidates_raw = cursor.fetchall()
    conn.close()

    scored_candidates = []
    for c in candidates_raw:
        track_id, filename, filepath, duration, track_bpm, usage_count = c
        
        score = 100
        
        # Usage Penalty (heavy penalty to prioritize new music)
        score -= (usage_count * 20)
        
        # BPM Weighting
        if track_bpm >= min_bpm and track_bpm <= max_bpm:
            score += 30 # Perfect match
        elif track_bpm >= min_bpm - 10 and track_bpm <= max_bpm + 10:
            score += 10 # Close fit
        else:
            score -= 10 # Far fit
            
        # Random jitter to mix things up slightly among similar scores
        score += random.uniform(-5, 5)
        
        scored_candidates.append({
            'data': c,
            'score': score
        })
        
    # Sort by score descending
    scored_candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # The 1/3 Rule: Create a unique block of 1/3 duration and loop it.
    full_target_duration_sec = duration_hours * 3600
    unique_block_target_sec = full_target_duration_sec / 3
    
    current_duration = 0
    selected_tracks = []
    
    # Selection loop
    for item in scored_candidates:
        if current_duration >= unique_block_target_sec:
            break
            
        track = item['data']
        # track structure: id, filename, filepath, duration, bpm, usage_count
        
        # Check for duplicates by filename
        is_duplicate = False
        for s in selected_tracks:
            if s['filename'] == track[1]:
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
            
        selected_tracks.append({
            'id': track[0],
            'filename': track[1],
            'filepath': track[2],
            'duration': track[3],
            'bpm': track[4],
            'artist': "Unknown", 
            'title': track[1]
        })
        current_duration += track[3]
    
    logging.info(f"Selected {len(selected_tracks)} tracks. Unique Block: {current_duration/60:.1f} min (Target 1/3: {unique_block_target_sec/60:.1f} min). Full Video: {duration_hours}h.")
    
    if len(selected_tracks) == 0:
        logging.error("No tracks selected!")
        return

    # Shuffle slightly within blocks to maintain freshness but keep rough order? 
    # Actually user said "don't fully randomly choose", "try to use newly downloaded music".
    # Our sorting `ORDER BY usage_count ASC, date_added DESC` achieves this.
    # We might want to shuffle small blocks to avoid same artist back-to-back if possible, 
    # but exact strict ordering by "newness" might be better for "new content".
    # Let's keep the order from the DB query which prioritizes new/unused.
    
    output_data = {
        'unique_block_duration': current_duration,
        'full_target_duration': full_target_duration_sec,
        'tracks': selected_tracks
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)
    logging.info(f"Selection saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, choices=[1, 3], default=1, help="Duration in hours")
    args = parser.parse_args()
    
    select_music('idea.json', 'selected_tracks.json', args.hours)

