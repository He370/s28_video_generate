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
chmod +x automation/workflows/*.sh
chmod +x automation/schedules/*.sh
```

## Mac Cron Setup

We use a Python script to manage cron jobs to ensure consistency and ease of updates.

### 1. Define Schedules

All cron schedules are defined in `automation/schedules/cron_schedules.txt`.

To add or modify a job:
1.  Open `automation/schedules/cron_schedules.txt`.
2.  Add your cron entry. Lines starting with `#` are comments.

Example entry:
```text
# History Story - Daily at 2:00 AM
0 2 * * * /Users/leo/Documents/antigravity/s28_video_generate/venv/bin/python3 /Users/leo/Documents/antigravity/s28_video_generate/automation/run_job.py --project history_story --command "/Users/leo/Documents/antigravity/s28_video_generate/automation/workflows/history_story_biography.sh"
```

### 2. Apply Schedules

Run the `set_cron.py` script to update your system's crontab based on the text file. This script is idempotent (safe to run multiple times).

```bash
venv/bin/python automation/set_cron.py
```

### 3. Verify

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
