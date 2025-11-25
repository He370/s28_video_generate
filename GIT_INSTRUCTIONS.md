# Git Workflow Instructions for Video Generation Project

This document provides a guide on how to manage this project using Git, including initial setup, collaboration on other machines, and a cheatsheet for common commands.

## 1. Initial Setup (Upload to Git)

Since this project is not yet a Git repository, follow these steps to initialize it and push it to a remote repository (e.g., GitHub, GitLab).

### Prerequisites
- You have `git` installed on your machine.
- You have an account on a Git hosting service (e.g., GitHub).

### Steps
1.  **Initialize Git:**
    Open your terminal in the project root (`/Users/Leo/Documents/antigravity/video_generate`) and run:
    ```bash
    git init
    ```

2.  **Create/Verify .gitignore:**
    Ensure you have a `.gitignore` file to prevent uploading large video files, temporary assets, or sensitive secrets. A basic `.gitignore` has been created for you.

3.  **Stage and Commit Files:**
    Add all your project files to the staging area:
    ```bash
    git add .
    ```
    Commit the files:
    ```bash
    git commit -m "Initial commit: Video generation project structure"
    ```

4.  **Create a Remote Repository:**
    - Go to GitHub (or your preferred provider) and create a new **empty** repository.
    - Do *not* initialize it with a README, license, or gitignore (you already have these locally).

5.  **Link and Push:**
    Copy the URL of your new repository (e.g., `https://github.com/username/video-generate.git`) and run:
    ```bash
    git remote add origin <YOUR_REPO_URL>
    git branch -M main
    git push -u origin main
    ```

---

## 2. Pulling on Another Mac

To work on this project on a different machine:

1.  **Clone the Repository:**
    ```bash
    git clone <YOUR_REPO_URL>
    cd video-generate
    ```

2.  **Setup Environment:**
    - Install Python dependencies (ensure you have a `requirements.txt` or install manually).
    - **Important:** Re-create any secrets files (e.g., `.env`, `client_secrets.json`) that were ignored by `.gitignore`. You will need to copy these securely from your original machine or generate new ones.

---

## 3. Git Cheatsheet & Version Control

### Daily Workflow

**1. Check Status:**
See which files have changed.
```bash
git status
```

**2. Pull Latest Changes:**
Before starting work, always get the latest updates.
```bash
git pull origin main
```

**3. Stage Changes:**
Prepare files for committing.
```bash
# Add specific file
git add path/to/file.py

# Add all changed files
git add .
```

**4. Commit Changes:**
Save your changes with a descriptive message.
```bash
git commit -m "Description of what I changed"
```

**5. Push Changes:**
Upload your commits to the remote server.
```bash
git push origin main
```

### Handling Conflicts
If `git pull` fails due to conflicts:
1.  Open the conflicting files.
2.  Look for `<<<<<<<`, `=======`, `>>>>>>>` markers.
3.  Edit the code to resolve the conflict (choose one version or merge them).
4.  Save the file.
5.  Run `git add <file>` and `git commit`.

### Branching (Recommended for New Features)
Instead of working directly on `main`, use branches.

**Create and switch to a new branch:**
```bash
git checkout -b feature/new-horror-story
```

**Work, add, and commit as usual.**

**Push the branch:**
```bash
git push -u origin feature/new-horror-story
```

**Merge back to main (via Pull Request on GitHub or locally):**
```bash
git checkout main
git pull origin main
git merge feature/new-horror-story
```
