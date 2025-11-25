import os
import json
import pickle
import random
import time
import http.client
import httplib2

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
  http.client.IncompleteRead, http.client.ImproperConnectionState,
  http.client.CannotSendRequest, http.client.CannotSendHeader,
  http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

class YouTubeUploader:
    def __init__(self, client_secrets_file="client_secrets.json", token_file="token.pickle"):
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.youtube = None

    def authenticate(self):
        """
        Authenticates the user and creates a YouTube API client.
        """
        credentials = None
        
        # Load existing credentials if available
        if os.path.exists(self.token_file):
            print(f"Loading credentials from {self.token_file}...")
            with open(self.token_file, 'rb') as token:
                credentials = pickle.load(token)

        # Refresh or create new credentials
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("Refreshing access token...")
                credentials.refresh(Request())
            else:
                print("Fetching new tokens...")
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(f"Client secrets file not found: {self.client_secrets_file}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes
                )
                # Use fixed port 8080 to ensure the redirect URI matches what is registered in Google Cloud Console
                # You must add "http://localhost:8080/" to the "Authorized redirect URIs" in your Google Cloud Console credentials.
                try:
                    credentials = flow.run_local_server(port=8080)
                except KeyboardInterrupt:
                    print("\nAuthentication cancelled by user.")
                    return

            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(credentials, token)
                print(f"Credentials saved to {self.token_file}")

        self.youtube = build(self.api_service_name, self.api_version, credentials=credentials)
        print("Authentication successful.")

    def upload_video(self, file_path, title, description, category_id="22", privacy_status="private", tags=None):
        """
        Uploads a video to YouTube with robust error handling and retries.
        """
        if not self.youtube:
            raise ValueError("Not authenticated. Call authenticate() first.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        print(f"Uploading {file_path} to YouTube...")
        print(f"Title: {title}")
        print(f"Privacy: {privacy_status}")
        
        if tags is None:
            tags = ['s28']

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        # Chunk size: 4MB
        media = MediaFileUpload(file_path, chunksize=4*1024*1024, resumable=True)
        
        insert_request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        return self._resumable_upload(insert_request)

    def upload_thumbnail(self, video_id, file_path):
        """
        Uploads a thumbnail to a YouTube video.
        """
        if not self.youtube:
            raise ValueError("Not authenticated. Call authenticate() first.")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Thumbnail file not found: {file_path}")
            
        print(f"Uploading thumbnail from {file_path} for video {video_id}...")
        
        media = MediaFileUpload(file_path, mimetype='image/png', resumable=True)
        
        request = self.youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Thumbnail upload {int(status.progress() * 100)}%")
        
        print("Thumbnail uploaded successfully.")
        return response

    def _resumable_upload(self, insert_request):
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print("Uploading file...")
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print(f"Video id '{response['id']}' was successfully uploaded.")
                        return response
                    else:
                        raise Exception(f"The upload failed with an unexpected response: {response}")
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%")
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                else:
                    raise
            except RETRIABLE_EXCEPTIONS as e:
                error = f"A retriable error occurred: {e}"

            if error is not None:
                print(error)
                retry += 1
                if retry > MAX_RETRIES:
                    raise Exception("No longer attempting to retry.")

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print(f"Sleeping {sleep_seconds} seconds and then retrying...")
                time.sleep(sleep_seconds)

if __name__ == "__main__":
    # Example usage
    try:
        uploader = YouTubeUploader()
        uploader.authenticate()
        # uploader.upload_video("path/to/video.mp4", "Test Video", "This is a test.")
    except Exception as e:
        print(f"Error: {e}")
