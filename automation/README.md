# Automation Module

This module handles the scheduling and automated execution of video generation and uploading tasks. It includes error monitoring and email notifications.

## Prerequisites

- **Python 3.9+**
- **Google Cloud Credentials**: `client_secrets.json` and `token.pickle` must be present in `video_uploader/` and authorized.
- **SMTP Credentials**: A Gmail account with an App Password for sending notifications.

## Setup

### 1. Configuration

Create or update `automation/config.json` with your email credentials:

```json
{
    "email": {
        "sender_email": "ldh.sjtu+alert@gmail.com",
        "sender_password": "joeo sowq wkvl srug",
        "recipient_email": "ldh.sjtu+alert@gmail.com",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587
    }
}
```

> **Note**: For Gmail, you must generate an [App Password](https://myaccount.google.com/apppasswords) if you have 2FA enabled. Do not use your regular password.

### 2. Make Scripts Executable

Ensure the workflow scripts are executable:

```bash
chmod +x automation/workflows/history_story_daily.sh
chmod +x automation/workflows/today_history_daily.sh
chmod +x automation/workflows/horror_story_daily.sh
chmod +x automation/workflows/white_noise_daily.sh
```

## Mac Cron Setup

To schedule the jobs to run automatically on your Mac, use `crontab`.

1.  **Open Crontab Editor**:
    ```bash
    crontab -e
    ```

2.  **Add Schedule Entries**:
    Add the following lines to schedule the jobs. This example runs `today_history` at 8:00 AM and `history_story` at 8:00 PM daily.

    **Important**: You must provide the full path to `python3` and the project directory.

    ```bash
    # Horror Story 1 - Daily at 0:00 AM
    0 0 * * * /Users/leo/Documents/antigravity/s28_video_generate/venv/bin/python3 /Users/leo/Documents/antigravity/s28_video_generate/automation/run_job.py --project horror_story --command "/Users/leo/Documents/antigravity/s28_video_generate/automation/workflows/horror_story_daily.sh"

    # Horror Story 2 - Daily at 1:28 AM
    28 1 * * * /Users/leo/Documents/antigravity/s28_video_generate/venv/bin/python3 /Users/leo/Documents/antigravity/s28_video_generate/automation/run_job.py --project horror_story --command "/Users/leo/Documents/antigravity/s28_video_generate/automation/workflows/horror_story_daily.sh"

    # Horror Story 3 - Daily at 2:28 AM
    28 2 * * * /Users/leo/Documents/antigravity/s28_video_generate/venv/bin/python3 /Users/leo/Documents/antigravity/s28_video_generate/automation/run_job.py --project horror_story --command "/Users/leo/Documents/antigravity/s28_video_generate/automation/workflows/horror_story_daily.sh"

    # History Story - Daily at 6:00 AM
    0 6 * * * /Users/leo/Documents/antigravity/s28_video_generate/venv/bin/python3 /Users/leo/Documents/antigravity/s28_video_generate/automation/run_job.py --project history_story --command "/Users/leo/Documents/antigravity/s28_video_generate/automation/workflows/history_story_daily.sh"

    # History Story - Daily at 7:00 AM
    0 7 * * * /Users/leo/Documents/antigravity/s28_video_generate/venv/bin/python3 /Users/leo/Documents/antigravity/s28_video_generate/automation/run_job.py --project history_story --command "/Users/leo/Documents/antigravity/s28_video_generate/automation/workflows/history_story_daily.sh"

    # Today History - Daily at 6:00 PM
    0 18 * * * /Users/leo/Documents/antigravity/s28_video_generate/venv/bin/python3 /Users/leo/Documents/antigravity/s28_video_generate/automation/run_job.py --project today_history --command "/Users/leo/Documents/antigravity/s28_video_generate/automation/workflows/today_history_daily.sh"

    # White Noise - Daily at 9:30 PM
    30 21 * * * /Users/leo/Documents/antigravity/s28_video_generate/venv/bin/python3 /Users/leo/Documents/antigravity/s28_video_generate/automation/run_job.py --project white_noise --command "/Users/leo/Documents/antigravity/s28_video_generate/automation/workflows/white_noise_daily.sh"
    ```

    *Note: We use the virtual environment's python executable to ensure all dependencies are available.*
    *Ensure the paths match your actual project location.*

3.  **Save and Exit**:
    - If using `vi`/`vim` (default): Press `Esc`, type `:wq`, and press `Enter`.
    - If using `nano`: Press `Ctrl+O`, `Enter`, then `Ctrl+X`.

4.  **Verify**:
    List your cron jobs to ensure they are saved:
    ```bash
    crontab -l
    ```

## Mac Permissions (Full Disk Access)

On macOS, `cron` may not have permission to access your Documents folder or run scripts. You need to grant **Full Disk Access** to `cron`.

1.  Open **System Settings** > **Privacy & Security** > **Full Disk Access**.
2.  Click the `+` button to add an application.
3.  Press `Cmd+Shift+G` to open the "Go to Folder" dialog.
4.  Type `/usr/sbin/cron` and press Enter.
5.  Select `cron` and click **Open**.
6.  Ensure the toggle next to `cron` is enabled.

## Testing

You can test the automation manually before scheduling:

```bash
# Test Today History Workflow
python3 automation/run_job.py --project today_history --command "automation/workflows/today_history_daily.sh"
```

Check `automation/logs/` for execution logs.
