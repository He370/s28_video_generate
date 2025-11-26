# Video Uploader

This module handles uploading generated videos to YouTube using the YouTube Data API v3. It supports multiple YouTube channels/credentials and includes tools for batch uploading and credential management.

## Features

-   **Batch Uploading**: Upload multiple videos from a project's queue.
-   **Multiple Accounts**: Support for multiple YouTube channels via profiles.
-   **Resumable Uploads**: Handles large file uploads reliably.
-   **Metadata**: Automatically sets title, description, tags, and privacy status.
-   **Thumbnail Upload**: Automatically uploads the first scene image as the thumbnail.
-   **Credential Management**: Scripts to refresh tokens for testing accounts.

## Setup

1.  **GCP Project**: Create a project in Google Cloud Console and enable the "YouTube Data API v3".
2.  **Credentials**: Create "OAuth 2.0 Client IDs" (Desktop app).
3.  **Download JSON**: Download the client secret JSON file.
4.  **Install**: Place the JSON file in this directory (`video_uploader/`).
    *   Default: `client_secrets.json`
    *   Profile: `client_secrets_<profile_name>.json` (e.g., `client_secrets_horror.json`)

## Usage

### Batch Upload

Upload videos for a specific project.

```bash
# Upload 1 video from 'today_history' project using default credentials
python video_uploader/batch_upload.py today_history

# Upload 3 videos to 'horror' channel
python video_uploader/batch_upload.py horror_story --count 3 --profile horror

# Upload as public (default is private)
python video_uploader/batch_upload.py today_history --privacy public
```

### Refresh Credentials

If your GCP project is in "Testing" mode, refresh tokens expire every 7 days. Use this script to refresh them.

```bash
# Refresh all found credentials
python video_uploader/refresh_credentials.py

# Force refresh (e.g., to switch accounts)
python video_uploader/refresh_credentials.py --force

# Refresh specific profile
python video_uploader/refresh_credentials.py --profile horror --force
python video_uploader/refresh_credentials.py --profile relax --force
```

See [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) for more details on managing multiple accounts.
