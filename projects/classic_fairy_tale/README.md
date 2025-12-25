# Classic Fairy Tale Project

This project generates animated/narrated videos of classic fairy tales using Gemini models.

## Features
- **Story Retrieval**: Automatically find stories from collections like "Grimms' Fairy Tales".
- **Reference Image**: Generates a consistency character sheet using `GEMINI_IMAGE_ADVANCED_MODEL`.
- **Automated Video Creation**: Full pipeline from script to video.

## Usage

### 1. Populate Story Queue
```bash
# Extract stories from Grimms' Fairy Tales (resources/grimms.txt)
python3 crawl_stories.py
```

### 2. Generate Videos
```bash
python3 main.py --count 1 --mode dev
```

### Playlist Management
The `crawl_stories.py` script automatically adds new playlist names to `projects/classic_fairy_tale/playlist.json`.
To automatically add uploaded videos to a playlist:
1. Open `projects/classic_fairy_tale/playlist.json`.
2. Find the playlist name (e.g., "Hans Christian Andersen").
3. Replace `null` with the **YouTube Playlist ID**.

### Automation
Use the provided script:
```bash
./classic_fairy_tale_daily.sh --search "Greek Myths" --count 1 --mode dev
```
