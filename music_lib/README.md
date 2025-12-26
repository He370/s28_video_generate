# Music Library Management

This directory contains scripts and assets for managing the music library used in video generation. It ingests music files and metadata into a SQLite database for easy querying.

## Setup

1.  **Dependencies**: Ensure you have the required Python packages installed.
    ```bash
    pip install mutagen
    ```

2.  **Directory Structure**:
    -   `music/assets/`: Place your downloaded `.mp3` files here.

## Usage

### Ingesting Music

Run the ingestion script to scan `music/assets` and popluate `music.db`.

```bash
python ingest_music.py
```

The script will:
1.  Scan `music/assets` for mp3 files.
2.  Read ID3 tags (Title, Artist, Genre, Mood, BPM) from the file using `mutagen`.
3.  If tags are missing, it falls back to parsing the filename.
4.  Store everything in `music.db`.

## Checking the Database

You can interact with the `music.db` using the `sqlite3` command-line tool.

### Common Commands

**1. Open the database:**
```bash
sqlite3 music.db
```

**2. List all tracks (limit 10):**
```sql
SELECT id, filename, genre, mood FROM tracks LIMIT 10;
```

**3. Check total number of tracks:**
```sql
SELECT COUNT(*) FROM tracks;
```

**4. Find tracks by Genre (e.g., Jazz):**
```sql
SELECT filename, duration FROM tracks WHERE genre LIKE '%Jazz%';
```

**5. Find tracks with "Unknown" metadata (Generic fallback):**
```sql
SELECT filename FROM tracks WHERE genre = 'Unknown';
```

**6. Show table schema:**
```sql
.schema tracks
```

## Database Schema

Table `tracks`:
-   `id`: INTEGER PRIMARY KEY
-   `filename`: TEXT (Unique)
-   `filepath`: TEXT
-   `genre`: TEXT
-   `mood`: TEXT
-   `bpm`: INTEGER
-   `duration`: INTEGER (seconds)
-   `date_added`: TIMESTAMP
-   `last_used`: TIMESTAMP
-   `usage_count`: INTEGER
