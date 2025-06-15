import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from pathlib import Path

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Get Gmail API service instance and credentials."""
    creds = None
    token_path = Path('token.pickle')
    
    # Load existing credentials if available
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or create new credentials if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    # Build and return Gmail service and credentials
    service = build('gmail', 'v1', credentials=creds)
    return service, creds

def check_credentials():
    """Check if valid credentials exist."""
    token_path = Path('token.pickle')
    if not token_path.exists():
        return False
    
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)
    
    return creds and creds.valid

def revoke_credentials():
    """Revoke and remove stored credentials."""
    token_path = Path('token.pickle')
    if token_path.exists():
        token_path.unlink() 