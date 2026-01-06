# Veo 3.1 Video Generation - Complete Fix

## Issue
Gemini API call for Veo video generation was failing with operation handling errors.

## Root Causes Identified

1. **Wrong API method**: Used `generate_content()` instead of `generate_videos()`
2. **Wrong config class**: Used `GenerateVideoConfig` instead of `GenerateVideosConfig` (plural)
3. **Incorrect operation polling**: Tried to use non-existent `operations.wait()` method
4. **Wrong response structure**: Didn't use `files.download()` to retrieve video

## Complete Fix Applied

### 1. Correct API Method
```python
response = self.client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=video_config
)
```

### 2. Correct Configuration
```python
video_config = types.GenerateVideosConfig(
    aspect_ratio="16:9",  # 1920x1080
    duration_seconds=8,   # 8-second video
)
```

### 3. Proper Async Operation Handling
Based on official documentation at: https://ai.google.dev/gemini-api/docs/video

```python
# Check if response is a long-running operation
if hasattr(response, 'name') and 'operations/' in response.name:
    operation = response
    
    # Poll using operations.get() method
    while not operation.done and elapsed < max_wait_time:
        time.sleep(poll_interval)
        elapsed += poll_interval
        
        # Refresh operation status
        operation = self.client.operations.get(operation)
        
        if not operation.done:
            print(f"Still generating... ({elapsed}s elapsed)")
    
    if operation.done:
        response = operation
```

### 4. Correct Video Extraction
```python
# Extract from completed operation
if hasattr(response, 'response') and hasattr(response.response, 'generated_videos'):
    generated_videos = response.response.generated_videos
    if generated_videos and len(generated_videos) > 0:
        video = generated_videos[0]
        
        # Download using files.download()
        self.client.files.download(file=video.video)
        video.video.save(output_path)
```

## Key Changes from Official Documentation

1. **Use `client.operations.get(operation)`** - NOT `operations.wait()`
2. **Poll with `while not operation.done`** - Check the `.done` attribute
3. **Extract from `operation.response.generated_videos`** - Nested structure
4. **Download with `client.files.download()`** - Don't access bytes directly

## Testing

The fix follows the exact pattern from Google's official Veo documentation:
- Creates long-running operation via `generate_videos()`
- Polls operation status with `operations.get()`
- Downloads completed video with `files.download()`
- Saves video with `.save()` method

## Settings

- **Model**: `veo-3.1-generate-preview`
- **Resolution**: 1080p (16:9 aspect ratio)
- **Duration**: 8 seconds
- **Poll Interval**: 10 seconds
- **Max Wait Time**: 600 seconds (10 minutes)
