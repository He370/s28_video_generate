# Music Video Generator

This project automates the creation of "Relax & Focus" style music videos using simple looped visuals and curated music playlists.

## Workflow
The process is orchestrated by `main.py` and tracks state in `videos.json`.

1.  **Idea Generation**: Queries the local music database to see what genres are available, then uses Gemini to generate a specific theme (e.g., "Midnight Metropolis Jazz"), title, description, and prompts for visuals.
2.  **Visuals Creation**: 
    *   Generates a high-quality static cover image using Gemini (Imagen 3).
    *   Generates a 4-second seamless video loop using Gemini (Veo) based on the cover image and prompts.
3.  **Music Selection**: Selects a set of tracks from `music.db` that match the generated genre and BPM criteria to fill the target duration (e.g., 1 hour). Prioritizes newer and less-used tracks.
4.  **Assembly**:
    *   Concatenates audio tracks into a single file with crossfades.
    *   Loops the video visual (using FFmpeg `stream_loop`) to match the audio duration.
    *   Muxes audio and video into the final MP4.

## Usage

### Setup
Ensure you are in the project root and the virtual environment is set up.

### Running
Use the `run.sh` script to generate a new video.

```bash
# Generate a 1-hour music video
./projects/music_video/run.sh 1

# Generate a 3-hour music video
./projects/music_video/run.sh 3
```

### Manual Execution
You can also run `main.py` directly:

```bash
# Add a new 1-hour video to the queue and process it
./venv/bin/python projects/music_video/main.py --add-new --hours 1 --count 1
```
