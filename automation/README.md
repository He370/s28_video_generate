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

To schedule the jobs to run automatically on your Mac, use `crontab`.

1.  **Open Crontab Editor**:
    ```bash
    crontab -e
    ```

2.  **Add Schedule Entries**:
    Add the following lines to schedule the jobs.
    
    **Important**: You must provide the full path to the scripts.

    ```bash
# 02:00 AM - Nightly Schedule (Horror Story)
0 2 * * * /Users/leo/Documents/antigravity/s28_video_generate/automation/schedules/0200_schedule.sh

# 04:00 AM - Nightly Schedule (Music Videos)
0 4 * * * /Users/leo/Documents/antigravity/s28_video_generate/automation/schedules/0400_schedule.sh

# 06:00 AM - History Story (What If)
0 6 * * * /Users/leo/Documents/antigravity/s28_video_generate/automation/schedules/0600_schedule.sh

# 10:00 AM - White Noise (1h)
0 10 * * * /Users/leo/Documents/antigravity/s28_video_generate/automation/schedules/1000_schedule.sh

# 12:00 PM - Today History
0 12 * * * /Users/leo/Documents/antigravity/s28_video_generate/automation/schedules/1200_schedule.sh

# 02:00 PM - History Story (Mystery)
0 14 * * * /Users/leo/Documents/antigravity/s28_video_generate/automation/schedules/1400_schedule.sh

# 04:00 PM - White Noise (8h)
0 16 * * * /Users/leo/Documents/antigravity/s28_video_generate/automation/schedules/1600_schedule.sh

# 06:00 PM - White Noise (3h)
0 18 * * * /Users/leo/Documents/antigravity/s28_video_generate/automation/schedules/1800_schedule.sh
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
