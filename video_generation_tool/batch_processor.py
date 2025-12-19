import json
import os
from datetime import datetime
from typing import List, Dict

def load_video_queue(json_path: str) -> List[Dict]:
    """
    Load the video queue from a JSON file.
    
    Args:
        json_path: Path to the videos.json file.
        
    Returns:
        List of video items.
    """
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Video queue file not found: {json_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing video queue JSON: {e}")
        return []

def save_video_queue(json_path: str, videos: List[Dict]) -> bool:
    """
    Save the video queue to a JSON file.
    
    Args:
        json_path: Path to the videos.json file.
        videos: List of video items.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        with open(json_path, 'w') as f:
            json.dump(videos, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving video queue: {e}")
        return False

def get_pending_videos(videos: List[Dict], count: int) -> List[Dict]:
    """
    Get N videos with status 'pending'.
    
    Args:
        videos: List of all video items.
        count: Number of pending videos to retrieve.
        
    Returns:
        List of pending video items (up to count).
    """
    pending = [v for v in videos if v.get('status') in ['pending']]
    return pending[:count]

def update_video_status(json_path: str, index: int, status: str, **kwargs) -> bool:
    """
    Update the status of a video in the queue.
    
    Args:
        json_path: Path to the videos.json file.
        index: Index of the video to update.
        status: New status value.
        **kwargs: Additional fields to update (e.g., date_updated, error_message).
        
    Returns:
        True if successful, False otherwise.
    """
    videos = load_video_queue(json_path)
    
    for video in videos:
        if video.get('index') == index:
            video['status'] = status
            video['date_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update any additional fields
            for key, value in kwargs.items():
                video[key] = value
            
            return save_video_queue(json_path, videos)
    
    print(f"Video with index {index} not found in queue")
    return False


def add_video_to_queue(json_path: str, video_item: Dict) -> bool:
    """
    Add a new video to the queue.
    Automatically assigns a new index.
    
    Args:
        json_path: Path to the videos.json file.
        video_item: Dictionary containing video configuration.
        
    Returns:
        True if successful, False otherwise.
    """
    videos = load_video_queue(json_path)
    
    # Determine new index
    if videos:
        max_index = max(v.get('index', 0) for v in videos)
        new_index = max_index + 1
    else:
        new_index = 1
        
    video_item['index'] = new_index
    video_item['status'] = 'pending'
    video_item['date_added'] = datetime.now().strftime('%Y-%m-%d')
    
    videos.append(video_item)
    
    return save_video_queue(json_path, videos)
