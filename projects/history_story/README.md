# History Story Video Generator

This project generates "What If" scenarios and "Ancient Civilization Mysteries" videos using AI. It uses Google's Gemini models for script writing and image generation, and Edge TTS for narration.

## Project Structure

- `idea_generator.py`: Generates new video topics and adds them to the queue.
- `main.py`: Processes the video queue and generates videos.
- `videos.json`: Stores the queue of videos to be generated.
- `output/`: Directory where generated videos and assets are saved.

## Setup

Ensure you have the required dependencies installed and the `video_generation_tool` package is accessible (usually by being in the parent directory).

## Usage

### 1. Generate Video Ideas

Run the idea generator to populate `videos.json` with new topics.

```bash
# Generate 5 new ideas (default mixed types, English)
python3 projects/history_story/idea_generator.py --count 5

# Generate specific types
python3 projects/history_story/idea_generator.py --count 3 --type what_if
python3 projects/history_story/idea_generator.py --count 3 --type mystery

# Generate in a different language
python3 projects/history_story/idea_generator.py --count 3 --language "French"
```

### 2. Generate Videos

Run the main script to process pending videos from the queue.

```bash
# Generate 1 video (Dev mode - faster, lower quality)
python3 projects/history_story/main.py --count 1 --mode dev

# Generate all pending videos (Prod mode - higher quality)
python3 projects/history_story/main.py --count 10 --mode prod
```

## Configuration

You can manually edit `videos.json` to adjust:
- `topic`: The subject of the video.
- `type`: `what_if` or `mystery`.
- `image_style`: The visual style prompt for image generation.
- `language`: The language for the script and audio.
