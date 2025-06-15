import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from utils.auth import get_gmail_service
import email
from typing import List, Dict, Any
import os
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

class EmailReader:
    def __init__(self, gmail_service=None):
        """Initialize the email reader with Gmail service."""
        if gmail_service is None:
            # If no service provided, create one using credentials
            credentials = Credentials.from_authorized_user_file(
                'token.pickle',
                ['https://www.googleapis.com/auth/gmail.readonly']
            )
            self.service = build('gmail', 'v1', credentials=credentials)
        else:
            self.service = gmail_service
    
    def get_threads(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent email threads."""
        try:
            results = self.service.users().threads().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            threads = results.get('threads', [])
            return self._process_threads(threads)
        except Exception as e:
            print(f"Error fetching threads: {e}")
            return []
    
    def _process_threads(self, threads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process thread data into a more usable format."""
        processed_threads = []
        
        for thread in threads:
            thread_data = self.service.users().threads().get(
                userId='me',
                id=thread['id']
            ).execute()
            
            messages = thread_data.get('messages', [])
            processed_messages = []
            
            for message in messages:
                msg_data = self._process_message(message)
                if msg_data:
                    processed_messages.append(msg_data)
            
            if processed_messages:
                processed_threads.append({
                    'thread_id': thread['id'],
                    'messages': processed_messages,
                    'snippet': thread_data.get('snippet', '')
                })
        
        return processed_threads
    
    def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual message data."""
        try:
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get message body
            body = self._get_message_body(message['payload'])
            
            return {
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body
            }
        except Exception as e:
            print(f"Error processing message: {e}")
            return None
    
    def _get_message_body(self, payload: Dict[str, Any]) -> str:
        """Extract message body from payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    return base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
        
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
        
        return ''
    
    def get_thread_by_id(self, thread_id: str) -> Dict[str, Any]:
        """Fetch a specific thread by ID."""
        try:
            thread_data = self.service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()
            
            messages = thread_data.get('messages', [])
            processed_messages = []
            
            for message in messages:
                msg_data = self._process_message(message)
                if msg_data:
                    processed_messages.append(msg_data)
            
            return {
                'thread_id': thread_id,
                'messages': processed_messages,
                'snippet': thread_data.get('snippet', '')
            }
        except Exception as e:
            print(f"Error fetching thread: {e}")
            return None

    def get_email_threads(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent email threads from Gmail.
        
        Args:
            max_results: Maximum number of threads to return
            
        Returns:
            List of email threads with their messages
        """
        try:
            # Get list of threads
            results = self.service.users().threads().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            threads = results.get('threads', [])
            thread_details = []
            
            for thread in threads:
                # Get full thread details
                thread_data = self.service.users().threads().get(
                    userId='me',
                    id=thread['id']
                ).execute()
                
                messages = thread_data.get('messages', [])
                thread_messages = []
                
                for message in messages:
                    msg_data = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    headers = msg_data['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    
                    # Get message body
                    if 'parts' in msg_data['payload']:
                        body = msg_data['payload']['parts'][0]['body'].get('data', '')
                    else:
                        body = msg_data['payload']['body'].get('data', '')
                    
                    thread_messages.append({
                        'id': message['id'],
                        'subject': subject,
                        'sender': sender,
                        'body': body,
                        'timestamp': msg_data['internalDate']
                    })
                
                thread_details.append({
                    'id': thread['id'],
                    'messages': thread_messages
                })
            
            return thread_details
            
        except Exception as e:
            print(f"Error fetching email threads: {e}")
            return [] 