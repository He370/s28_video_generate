import argparse
import subprocess
import sys
import os
import datetime
from email_notifier import EmailNotifier

def run_command(command, project_name):
    """Runs a shell command and captures output."""
    print(f"[{datetime.datetime.now()}] Starting job for {project_name}...")
    print(f"Command: {command}")
    
    try:
        # Run command and capture output
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(f"[{datetime.datetime.now()}] Job completed successfully.")
        print("Output:\n" + result.stdout)
        return True, result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now()}] Job failed with exit code {e.returncode}.")
        error_output = e.stdout if e.stdout else "No output captured."
        print("Error Output:\n" + error_output)
        return False, error_output
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Unexpected error: {e}")
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description="Run an automation job with error reporting.")
    parser.add_argument("--project", required=True, help="Name of the project (e.g., today_history)")
    parser.add_argument("--command", required=True, help="Shell command to execute")
    parser.add_argument("--log-dir", default="automation/logs", help="Directory to store logs")
    
    args = parser.parse_args()
    
    # Ensure log directory exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "..", args.log_dir)
    os.makedirs(log_dir, exist_ok=True)
    
    # Run the job
    success, output = run_command(args.command, args.project)
    
    # Save log
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    status = "success" if success else "failure"
    log_filename = f"{args.project}_{status}_{timestamp}.log"
    log_path = os.path.join(log_dir, log_filename)
    
    with open(log_path, "w") as f:
        f.write(f"Command: {args.command}\n")
        f.write(f"Date: {datetime.datetime.now()}\n")
        f.write("-" * 40 + "\n")
        f.write(output)
        
    print(f"Log saved to {log_path}")
    
    # Send email on failure
    if not success:
        print("Sending error alert...")
        notifier = EmailNotifier(config_path=os.path.join(base_dir, "config.json"))
        notifier.send_error_alert(args.project, output)
        sys.exit(1)

if __name__ == "__main__":
    main()
