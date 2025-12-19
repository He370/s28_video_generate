# Horror Story Project

This project generates horror stories (Urban Legends or Rules Horror) using Gemini for scripts and image prompts, and generates audio and video assets.

## Directory Structure
- `main.py`: Core logic for video generation.
- `idea_generator.py`: Generates new video ideas/topics.
- `reset_audio.py`: Utility to reset audio assets and video status for reprocessing.
- `test_tts.py`: Utility to test TTS prompts and voices.
- `videos.json`: Database of video items and their statuses.
- `output/`: Generated video files and assets.
- `BGM/`: Background music files.

## Workflows

### 1. Daily Generation
Runs the full pipeline: Generate Idea -> Generate Video -> Upload.
```bash
./automation/workflows/horror_story_daily.sh
```

### 2. Reprocessing Videos
If a video has issues (e.g., bad audio) and needs to be regenerated:

**Step 1: Reset the video**
Use `reset_audio.py` to delete the bad assets and set the status to `reprocess`.
```bash
# Reset a specific video (e.g., index 1)
python3 projects/horror_story/reset_audio.py --index 1

# Or reset ALL videos
python3 projects/horror_story/reset_audio.py --all
```

**Step 2: Run the Reprocess Workflow**
This will regenerate the video(s) and upload them.
```bash
./automation/workflows/horror_story_reprocess.sh
```

## Manual Usage

**Generate Ideas:**
```bash
python3 projects/horror_story/idea_generator.py --count 5
```

**Generate Videos:**
```bash
python3 projects/horror_story/main.py --count 1 --mode prod
```

**Test TTS:**
Test different prompts or voices for the TTS engine.
```bash
python3 projects/horror_story/test_tts.py --prompt "Read this fast: " --text "Hello world"
```
