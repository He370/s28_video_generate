# White Noise Project

This project generates long-form relaxation and focus videos consisting of a static, AI-generated scene and a looped mix of white noise sound effects.

## Features

-   **Idea Generation**: Uses Gemini to create scene descriptions (e.g., "Cozy library", "Spaceship engine room").
-   **Image Generation**: Creates a high-quality static image for the scene.
-   **Smart Audio Mixing**: Uses Gemini to select suitable sound effects from a local library and assigns volume levels.
-   **Audio Looping**: Automatically loops short sound clips to match the target video duration (default 30 mins).
-   **Caching**: Saves selected assets to `segments.json` to avoid regenerating images or re-selecting sounds on re-runs.

## Usage

### 1. Generate Ideas

Generate new video concepts and add them to the queue (`videos.json`).

```bash
# Generate 5 new ideas
python3 projects/white_noise/idea_generator.py --count 5

# Generate in prod mode (if applicable)
python3 projects/white_noise/idea_generator.py --count 5 --mode prod
```

### 2. Generate Video

Process the queue and generate videos.

```bash
# Generate 1 video in DEV mode (30 seconds duration)
python3 projects/white_noise/main.py --count 1 --mode dev

# Generate 1 video in PROD mode (Full duration, e.g., 30 mins)
python3 projects/white_noise/main.py --count 1 --mode prod
```

### 3. Upload (Optional)

Upload the generated video to YouTube.

```bash
# Upload 1 video using specific credentials
python3 video_uploader/batch_upload.py white_noise --count 1 --profile relax
```

## Directory Structure

-   `idea_generator.py`: Script to generate video topics.
-   `main.py`: Main script to generate the video.
-   `videos.json`: Queue of videos to be generated.
-   `output/`: Generated videos and assets.
    -   `video_X/`:
        -   `final_video.mp4`: The final output.
        -   `assets/`:
            -   `scene.png`: Generated background image.
            -   `segments.json`: Metadata about selected assets.
