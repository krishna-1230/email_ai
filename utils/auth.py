import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from pathlib import Path
import logging
from cachetools import LRUCache

# Disable the googleapiclient file_cache warning
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

# Gmail API and Google Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly', 
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar',         # Full access to Calendar
    'https://www.googleapis.com/auth/calendar.events'   # Full access to Calendar events
]

def get_gmail_service():
    """Get Gmail API service instance and credentials."""
    creds = None
    token_path = Path('token.pickle')
    
    # Check if we need to handle scope changes
    scope_expanded = False
    
    # Load existing credentials if available
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
            
        # Check if the credentials have the required scopes
        if creds and creds.valid:
            current_scopes = creds.scopes if hasattr(creds, 'scopes') else []
            missing_scopes = [scope for scope in SCOPES if scope not in current_scopes]
            
            if missing_scopes:
                logging.info(f"Need to update token with new scopes: {missing_scopes}")
                creds = None
                scope_expanded = True
    
    # Refresh or create new credentials if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if scope_expanded:
                logging.info("Creating new token with expanded scopes")
                if token_path.exists():
                    token_path.unlink()  # Remove the old token
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    # Build and return Gmail service and credentials with in-memory cache
    cache = LRUCache(maxsize=1024)
    service = build('gmail', 'v1', credentials=creds, cache=cache)
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