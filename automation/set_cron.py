import os
import subprocess
import sys

def get_current_crontab():
    """Returns the current crontab as a list of lines."""
    try:
        output = subprocess.check_output(['crontab', '-l'], stderr=subprocess.PIPE)
        return output.decode('utf-8').splitlines()
    except subprocess.CalledProcessError:
        # crontab -l returns exit code 1 if no crontab exists for user
        return []

def set_crontab(lines):
    """Sets the crontab to the given list of lines."""
    # Ensure newline at end
    content = '\n'.join(lines) + '\n'
    try:
        # run crontab - to set from stdin
        subprocess.run(['crontab', '-'], input=content.encode('utf-8'), check=True, stderr=subprocess.PIPE)
        print("Crontab updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update crontab: {e.stderr.decode('utf-8')}")
        sys.exit(1)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schedule_file = os.path.join(script_dir, 'schedules', 'cron_schedules.txt')

    if not os.path.exists(schedule_file):
        print(f"Error: Schedule file not found at {schedule_file}")
        sys.exit(1)

    print(f"Reading schedules from: {schedule_file}")
    
    with open(schedule_file, 'r') as f:
        new_schedule_lines = f.readlines()

    # Filter out empty lines for check, but generally we want to mirror the file
    valid_lines = [line.strip() for line in new_schedule_lines if line.strip()]
    
    if not valid_lines:
        print("Warning: Schedule file appears empty. This will clear the crontab.")
        # We proceed to clear it if that's the intention, or we could ask for confirmation. 
        # For automation script, we usually just execute.

    print("Overwriting crontab with schedules from file...")
    set_crontab(new_schedule_lines)
    print("Crontab successfully managed by cron_schedules.txt.")

if __name__ == "__main__":
    main()
