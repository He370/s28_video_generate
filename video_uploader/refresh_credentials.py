import os
import glob
import pickle
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def refresh_all_credentials(force=False, profile=None):
    """
    Finds all client_secrets_*.json files and refreshes/generates their corresponding tokens.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all client secret files
    # Pattern: client_secrets.json (default) or client_secrets_<profile>.json
    # Find all client secret files
    # Pattern: client_secrets.json (default) or client_secrets_<profile>.json
    if profile:
        specific_secret = os.path.join(base_dir, f"client_secrets_{profile}.json")
        if os.path.exists(specific_secret):
            secret_files = [specific_secret]
        else:
            # Fallback to default
            default_secret = os.path.join(base_dir, "client_secrets.json")
            if os.path.exists(default_secret):
                print(f"No specific client_secrets found for '{profile}', using default client_secrets.json")
                secret_files = [default_secret]
            else:
                print(f"No client_secrets file found for profile: {profile} and no default found.")
                return
    else:
        secret_files = glob.glob(os.path.join(base_dir, "client_secrets*.json"))
    
    if not secret_files:
        print("No client_secrets files found.")
        return

    print(f"Found {len(secret_files)} credential file(s).")

    for secret_file in secret_files:
        filename = os.path.basename(secret_file)
        print(f"\nProcessing {filename}...")
        
        # Determine profile name and token filename
        if filename == "client_secrets.json":
            if profile and profile != "default":
                # We are using default secrets for a specific profile
                token_file = os.path.join(base_dir, f"token_{profile}.pickle")
            else:
                profile = "default"
                token_file = os.path.join(base_dir, "token.pickle")
        else:
            # Extract profile from client_secrets_<profile>.json
            # len("client_secrets_") = 15, len(".json") = 5
            profile = filename[15:-5]
            token_file = os.path.join(base_dir, f"token_{profile}.pickle")
            
        print(f"Profile: {profile}")
        print(f"Target token file: {os.path.basename(token_file)}")
        
        
        authenticate_and_save(secret_file, token_file, force=force)

def authenticate_and_save(client_secrets_file, token_file, force=False):
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    credentials = None
    
    # Load existing credentials if available
    if os.path.exists(token_file):
        try:
            with open(token_file, 'rb') as token:
                credentials = pickle.load(token)
        except Exception as e:
            print(f"Error loading existing token: {e}")
            credentials = None

    # Refresh or create new credentials
    if force or not credentials or not credentials.valid:
        if not force and credentials and credentials.expired and credentials.refresh_token:
            print("Token expired, attempting refresh...")
            try:
                credentials.refresh(Request())
                print("Refresh successful.")
            except Exception as e:
                print(f"Refresh failed: {e}. Starting new authentication flow.")
                credentials = None
        
        if not credentials:
            print("Starting new authentication flow (check your browser)...")
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes
            )
            # Use fixed port 8080 to match GCP console configuration
            try:
                credentials = flow.run_local_server(port=8080)
            except Exception as e:
                print(f"Authentication failed: {e}")
                return

        # Save credentials
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
            print(f"Credentials saved to {os.path.basename(token_file)}")
    else:
        print("Credentials are valid. No action needed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh YouTube API credentials.")
    parser.add_argument("--force", action="store_true", help="Force refresh even if credentials are valid.")
    parser.add_argument("--profile", default=None, help="Refresh only a specific profile (e.g., 'horror').")
    args = parser.parse_args()

    try:
        refresh_all_credentials(force=args.force, profile=args.profile)
        print("\nAll done!")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
