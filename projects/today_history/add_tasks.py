import os
import sys
import argparse
from datetime import datetime, timedelta

# Add the project root to sys.path to allow imports from video_generation_tool
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from video_generation_tool import batch_processor

def generate_dates(start_date_str: str, count: int) -> list[str]:
    """Generate a list of dates starting from the given date."""
    dates = []
    try:
        # Try parsing with year first
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        try:
            # Try parsing without year (assume current year for calculation, but output without year)
            # Actually, for "November 25", we need a year to do timedelta math.
            # Let's assume the user provides YYYY-MM-DD for the start date to be precise,
            # or we default to "tomorrow" if not provided.
            pass
        except:
            pass
            
    current_date = start_date
    for _ in range(count):
        # Format as "Month Day" (e.g., "November 25")
        date_str = current_date.strftime("%B %d")
        dates.append(date_str)
        current_date += timedelta(days=1)
        
    return dates

def main():
    parser = argparse.ArgumentParser(description="Add new dates to Today History video queue.")
    parser.add_argument("--count", type=int, default=7, help="Number of days to add")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD). Defaults to tomorrow.")
    parser.add_argument("--language", type=str, default="English", help="Language for the videos")
    args = parser.parse_args()
    
    # Setup paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    videos_json_path = os.path.join(project_dir, "videos.json")
    
    try:
        # Determine start date
        if args.start_date:
            try:
                start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
            except ValueError:
                print("Error: Start date must be in YYYY-MM-DD format.")
                sys.exit(1)
        else:
            # Default to tomorrow
            start_dt = datetime.now() + timedelta(days=1)
        
        print(f"Adding {args.count} new video tasks starting from {start_dt.strftime('%Y-%m-%d')}...")
        
        # Generate dates
        dates_to_add = []
        current_dt = start_dt
        for _ in range(args.count):
            dates_to_add.append(current_dt.strftime("%B %d"))
            current_dt += timedelta(days=1)
            
        # Load existing to check for duplicates (optional, but good practice)
        existing_videos = batch_processor.load_video_queue(videos_json_path)
        existing_dates = set(v.get("date") for v in existing_videos if v.get("date"))
        
        added_count = 0
        for date_str in dates_to_add:
            if date_str in existing_dates:
                print(f"Skipping {date_str} (already exists)")
                continue
                
            # Create video item structure
            video_item = {
                "date": date_str,
                "language": args.language,
                "image_style": "cinematic, photorealistic, historical documentary style",
                "events": 10,
                "description": "Generate a history video for a specific date."
            }
            
            batch_processor.add_video_to_queue(videos_json_path, video_item)
            print(f"Added: {date_str}")
            added_count += 1
            
        print(f"\nSuccessfully added {added_count} new video tasks to videos.json")
        if added_count == 0 and args.count > 0:
            print("Warning: No new tasks were added. All specified dates might already exist or an issue occurred.")
            
    except Exception as e:
        print(f"Error adding tasks: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
