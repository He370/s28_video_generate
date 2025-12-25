import argparse
import os
import sys
import json
import re
import unicodedata
from typing import List, Dict

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool import batch_processor

def parse_grimms_file(file_path: str, output_dir: str) -> List[Dict]:
    """
    Parses the Grimms' Fairy Tales text file and extracts stories.
    """
    stories = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print(f"Parsing {file_path}...")
        
        # Regex for story titles: "1 The Frog-King"
        # strip() is called on the line before matching, so it matches " 1 Title" (TOC) and "1 Title" (Body)
        title_pattern = re.compile(r'^(\d+)\s+([A-Za-z].+)$')
        
        current_story_number = 0
        current_title = ""
        current_text = []
        
        for line in lines:
            line_stripped = line.strip()
            match = title_pattern.match(line_stripped)
            
            if match:
                number = int(match.group(1))
                title = match.group(2).strip()
                
                # Check for sequence restart (handling Table of Contents vs Body)
                if number == 1:
                     # If we find Story 1, we always restart.
                     # If we had a previous sequence (e.g. TOC), we discard it unless it was real stories.
                     # The TOC usually has short text between items (0 lines).
                     if current_story_number > 0:
                         full_text_len = sum(len(x) for x in current_text)
                         if full_text_len > 1000: # Heuristic: Real stories are long
                             print(f"Saving end of previous sequence (Story {current_story_number})")
                             story_data = save_story(current_story_number, current_title, current_text, output_dir)
                             if story_data:
                                 stories.append(story_data)
                         else:
                             print("Discarding previous sequence (likely Table of Contents).")
                             # Clear extracted stories if they were from TOC?
                             # Since we are restarting, we assume previous loop was TOC.
                             # But 'stories' list accumulates valid saved stories.
                             # If we saved anything from TOC (unlikely due to heuristics), we might keep it?
                             # Actually save_story checks length > 100.
                             # TOC items usually have 0 length text.
                             pass
                     
                     print(f"Found sequence start: Story 1: {title}")
                     current_story_number = 1
                     current_title = title
                     current_text = []
                     continue

                if number == current_story_number + 1:
                    # Save previous story
                    if current_story_number > 0:
                        story_data = save_story(current_story_number, current_title, current_text, output_dir)
                        if story_data:
                            stories.append(story_data)
                    
                    # Start new story
                    current_story_number = number
                    current_title = title
                    current_text = []
                    # Print every 10 stories to reduce noise
                    if number % 10 == 0:
                        print(f"Found Story {number}: {title}")
                    continue
            
            # If we are inside a story, append lines
            if current_story_number > 0:
                # Skip blank lines at the start
                if not current_text and not line_stripped:
                    continue
                current_text.append(line)
        
        # Save the last story
        if current_story_number > 0:
             story_data = save_story(current_story_number, current_title, current_text, output_dir)
             if story_data:
                stories.append(story_data)
                
    except Exception as e:
        print(f"Error parsing file: {e}")
        import traceback
        traceback.print_exc()
        
    return stories

def clean_text(text: str, remove_parens: bool = False) -> str:
    """
    Normalizes text to ASCII and optionally removes parenthetical content.
    """
    if remove_parens:
        # Remove (...) content often used for alternative titles or German titles
        text = re.sub(r'\s*\(.*?\)', '', text)
    
    # Normalize unicode characters to closest ASCII equivalent
    # e.g. "Märchen" -> "Marchen"
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    
    # Clean up excessive whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def save_story(number: int, title: str, lines: List[str], output_dir: str) -> Dict:
    """Saves the story text to a file and returns the metadata dict."""
    
    full_text = "".join(lines)
    
    # Clean content: Normalize UTF-8 characters
    # We do NOT remove parentheses from content, only normalize chars
    cleaned_content = clean_text(full_text, remove_parens=False)
    
    # Heuristic check: ignore very short texts (might be fragments or TOC)
    if len(cleaned_content) < 500: # Increased threshold to avoid TOC garbage
        return None
    
    # Clean title for topic/filename: Remove (...) and normalize
    cleaned_title = clean_text(title, remove_parens=True)
    
    # Clean title for filename (snake_case)
    safe_title = "".join([c if c.isalnum() else "_" for c in cleaned_title])
    safe_title = re.sub(r'_+', '_', safe_title).strip('_')
    
    filename = f"{number:03d}_{safe_title}.txt"
    file_path = os.path.join(output_dir, filename)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
        
    # Generate a description
    # Use first paragraph or so
    paras = cleaned_content.split('\n\n')
    description = paras[0].replace('\n', ' ') if paras else cleaned_content[:200]
    if len(description) > 300:
        description = description[:300] + "..."
    
    word_count = len(cleaned_content.split())
    
    return {
        "topic": cleaned_title,
        "playlist_name": "Grimms' Fairy Tales",
        "description": description,
        "original_story_path": file_path,
        "source_id": number,
        "word_count": word_count
    }

def main():
    parser = argparse.ArgumentParser(description="Extract stories from Grimms' Fairy Tales text file.")
    parser.add_argument("--file", default=None, help="Path to the grimms.txt file")
    args = parser.parse_args()
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Default file path
    if args.file:
        file_path = args.file
    else:
        file_path = os.path.join(project_dir, "resources", "grimms.txt")
        
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return
        
    stories_dir = os.path.join(project_dir, "stories")
    if not os.path.exists(stories_dir):
        os.makedirs(stories_dir)
        
    videos_json_path = os.path.join(project_dir, "videos.json")
    
    # Parse and extract
    stories = parse_grimms_file(file_path, stories_dir)
    
    if not stories:
        print("No stories extracted.")
        return
        
    print(f"Extracted {len(stories)} stories.")
    
    # Add to videos.json
    added_count = 0
    # Load existing to check for duplicates
    existing_videos = batch_processor.load_video_queue(videos_json_path)
    existing_topics = {v.get('topic') for v in existing_videos}
    
    for story in stories:
        if story['topic'] in existing_topics:
            continue
            
        video_item = {
            "topic": story["topic"],
            "type": "classic_fairy_tale",
            "description": story["description"],
            "playlist_name": story["playlist_name"],
            "language": "English",
            "events": 8,
            "debug_scene_limit": None,
            "original_story_path": story["original_story_path"],
            "word_count": story.get("word_count", 0)
        }
        
        batch_processor.add_video_to_queue(videos_json_path, video_item)
        added_count += 1
        
    print(f"Successfully added {added_count} new stories to videos.json")
    
    # Update playlist.json
    metadata_path = os.path.join(project_dir, "playlist.json")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except:
            pass
    
    if "Grimms' Fairy Tales" not in metadata:
        metadata["Grimms' Fairy Tales"] = None
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        print("Added 'Grimms' Fairy Tales' to playlist.json")

if __name__ == "__main__":
    main()
