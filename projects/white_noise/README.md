# White Noise Project

This project generates long-form relaxation and focus videos consisting of a static, AI-generated scene and a looped mix of white noise sound effects.

## Features

-   **Dynamic Concept Generation**: Uses Gemini (Advanced Model) to analyze available sound effects and generate a matching video concept (Topic, Scene, Art Style) and select the best sounds in a single step.
-   **Tuned Image Prompts**: Generates detailed, optimized prompts for high-quality image generation.
-   **Smart Audio Mixing**: Automatically loops short sound clips to match the target video duration and mixes them at AI-suggested volume levels.
-   **Caching**: Saves selected assets to `segments.json` to avoid regenerating images or re-selecting sounds on re-runs.
-   **Metadata Generation**: Automatically generates YouTube titles, descriptions, and tags.

## Usage

### 1. Schedule Videos

Add placeholder entries to the queue (`videos.json`). This step defines the duration but leaves the creative details to be generated later.

```bash
# Add 1 placeholder video with 30 minutes duration
python3 projects/white_noise/idea_generator.py --count 1 --duration 30

# Add 5 placeholders with 60 minutes duration
python3 projects/white_noise/idea_generator.py --count 5 --duration 60
```

### 2. Generate Video

Process the queue. This step will:
1.  Pick up a pending video placeholder.
2.  Analyze your `audio_generater/extracted_sounds` library.
3.  Generate a unique concept (e.g., "Rainy Cafe") and select matching sounds.
4.  Generate a background image.
5.  Render the final video.

```bash
# Generate 1 video in DEV mode (Limited to 30 seconds for testing)
python3 projects/white_noise/main.py --count 1 --mode dev

# Generate 1 video in PROD mode (Full duration)
python3 projects/white_noise/main.py --count 1 --mode prod
```

### 3. Upload (Optional)

Upload the generated video to YouTube.

```bash
# Upload 1 video using specific credentials
python3 video_uploader/batch_upload.py white_noise --count 1 --profile relax
```

## Directory Structure

-   `idea_generator.py`: Script to add video placeholders to the queue.
-   `main.py`: Main script to generate the concept, assets, and video.
-   `videos.json`: Queue of videos to be generated.
-   `output/`: Generated videos and assets.
    -   `video_X/`:
        -   `video_X.mp4`: The final output.
        -   `assets/`:
            -   `scene.png`: Generated background image.
            -   `segments.json`: Metadata about selected assets and concept.
