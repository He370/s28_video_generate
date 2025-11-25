# Today in History Video Generator

This project generates "Today in History" videos using AI. It creates a video highlighting significant historical events for a specific date.

## Project Structure

- `add_tasks.py`: Adds new dates to the video queue.
- `main.py`: Processes the video queue and generates videos.
- `videos.json`: Stores the queue of videos to be generated.
- `output/`: Directory where generated videos and assets are saved.

## Setup

Ensure you have the required dependencies installed and the `video_generation_tool` package is accessible.

## Usage

### 1. Add Video Tasks

Run the task adder to populate `videos.json` with upcoming dates.

```bash
# Add next 7 days (starting from tomorrow)
python3 projects/today_history/add_tasks.py --count 7

# Add specific dates starting from a given date
python3 projects/today_history/add_tasks.py --count 5 --start-date 2025-12-01

# Add tasks in a different language
python3 projects/today_history/add_tasks.py --count 3 --language "Spanish"
```

### 2. Generate Videos

Run the main script to process pending videos from the queue.

```bash
# Generate 1 video (Dev mode - faster, lower quality)
python3 projects/today_history/main.py --count 1 --mode dev

# Generate all pending videos (Prod mode - higher quality)
python3 projects/today_history/main.py --count 10 --mode prod
```

## Configuration

You can manually edit `videos.json` to adjust:
- `date`: The date for the video (e.g., "November 25").
- `events`: Number of historical events to include.
- `image_style`: The visual style prompt for image generation.
- `language`: The language for the script and audio.
