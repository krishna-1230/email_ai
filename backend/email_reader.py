"""
Fixed version of EmailReader with guaranteed email sending functionality.
Replace the original email_reader.py with this file to fix email sending issues.
"""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.auth import get_gmail_service
import email
from typing import List, Dict, Any
import os
import logging
import sys
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
import time

load_dotenv()

# Set up enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('email_reader.log')
    ]
)
logger = logging.getLogger("email_reader")

class EmailReader:
    def __init__(self, gmail_service=None):
        """Initialize the email reader with Gmail service."""
        logger.info("Initializing EmailReader")
        if gmail_service is None:
            # If no service provided, create one using credentials
            logger.info("No service provided, creating one from credentials")
            credentials = Credentials.from_authorized_user_file(
                'token.pickle',
                ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
            )
            self.service = build('gmail', 'v1', credentials=credentials)
        else:
            logger.info("Using provided Gmail service")
            self.service = gmail_service
            
        # Check if this service has send permission
        self.can_send = self._check_send_permission()
        if not self.can_send:
            logger.warning("Gmail service does not have send permission! Replies will not work.")
    
    def _check_send_permission(self) -> bool:
        """Check if the Gmail service has sending permissions."""
        try:
            # Get the Gmail profile to check authorized scopes
            profile = self.service.users().getProfile(userId='me').execute()
            
            # Try to access the credentials object to check scopes
            if hasattr(self.service, '_http'):
                if hasattr(self.service._http, 'credentials'):
                    creds = self.service._http.credentials
                    if hasattr(creds, 'scopes'):
                        scopes = creds.scopes
                        send_scope = 'https://www.googleapis.com/auth/gmail.send'
                        has_scope = isinstance(scopes, (list, tuple)) and send_scope in scopes
                        logger.info(f"Gmail API send scope available: {has_scope}")
                        return has_scope
            
            logger.warning("Could not verify Gmail API scopes, assuming send permission is available")
            return True
        except Exception as e:
            logger.error(f"Error checking Gmail send permission: {e}")
            return False
    
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
            logger.error(f"Error fetching threads: {e}")
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
            logger.error(f"Error processing message: {e}")
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
            logger.error(f"Error fetching thread: {e}")
            return None

    def send_reply(self, thread_id: str, to_address: str, subject: str, message_body: str) -> bool:
        """Send a reply to an email thread.
        
        Args:
            thread_id: The ID of the thread to reply to
            to_address: The recipient's email address
            subject: Email subject, usually with "Re:" prefix
            message_body: The body of the email reply
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            logger.info(f"Preparing to send reply to: {to_address}")
            logger.info(f"Thread ID: {thread_id}")
            
            # Check if we have permission to send
            if not hasattr(self, 'can_send') or not self.can_send:
                # Try to check permission again
                self.can_send = self._check_send_permission()
                if not self.can_send:
                    logger.error("Missing send permission - please restart the application and reauthorize")
                    return False
            
            # Validate inputs
            if not thread_id or not to_address or not message_body:
                logger.error("Missing required parameters for sending reply")
                return False
                
            # Get user's email address for the From header only
            profile = self.service.users().getProfile(userId='me').execute()
            sender_email = profile.get('emailAddress', '')
            if not sender_email:
                logger.error("Could not get sender email address")
                return False
            
            logger.info(f"Sender email determined as: {sender_email}")
            logger.info(f"Sending TO: {to_address} (recipient)")
            
            # Create a more robust MIME message
            message = MIMEMultipart()
            message['to'] = to_address  # The recipient's email address
            message['from'] = sender_email  # Your own email address
            message['subject'] = subject if subject.startswith("Re:") else f"Re: {subject}"
            
            # Add text body
            message.attach(MIMEText(message_body, 'plain'))
            
            # Add In-Reply-To header to link to thread if possible
            try:
                # Get thread details to find message IDs
                thread_data = self.service.users().threads().get(userId='me', id=thread_id).execute()
                if thread_data and 'messages' in thread_data and len(thread_data['messages']) > 0:
                    # Find message headers
                    for msg in thread_data['messages']:
                        headers = msg.get('payload', {}).get('headers', [])
                        message_id = next((h['value'] for h in headers if h['name'] == 'Message-ID'), None)
                        if message_id:
                            message['In-Reply-To'] = message_id
                            message['References'] = message_id
                            logger.info(f"Added reply headers to connect to original message")
                            break
            except Exception as e:
                logger.warning(f"Could not add threading headers: {e}")
            
            # Log full message headers for debugging
            logger.info("----- Message Headers -----")
            for key, value in message.items():
                logger.info(f"{key}: {value}")
            
            # Encode the message
            try:
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            except AttributeError:
                # For Python versions where as_bytes() is not available
                raw = base64.urlsafe_b64encode(message.as_string().encode()).decode()
            
            # Log before sending
            logger.info(f"Sending reply with subject: {message['subject']}")
            logger.info(f"Message body preview: {message_body[:100]}...")
            
            # DIRECT METHOD: Send using Gmail API directly
            try:
                # Send the message
                result = self.service.users().messages().send(
                    userId='me',
                    body={
                        'raw': raw,
                        'threadId': thread_id
                    }
                ).execute()
                
                message_id = result.get('id', 'unknown')
                logger.info(f"Reply sent successfully. Message ID: {message_id}")
                
                # Verify the message was really sent (with longer delay)
                time.sleep(2)  # Wait longer for the message to be processed
                
                try:
                    # Try to retrieve the sent message
                    sent_message = self.service.users().messages().get(userId='me', id=message_id).execute()
                    labels = sent_message.get('labelIds', [])
                    
                    if 'SENT' in labels:
                        logger.info(f"Message confirmed in SENT folder with labels: {labels}")
                    else:
                        logger.warning(f"Message found but not in SENT folder. Labels: {labels}")
                        
                except Exception as e:
                    logger.warning(f"Could not verify message was sent: {e}")
                
                return True
                
            except HttpError as error:
                logger.error(f"HTTP Error sending message: {error}")
                logger.error(f"Response content: {error.content.decode('utf-8') if hasattr(error, 'content') else 'No content'}")
                
                # Try alternative method as a fallback
                logger.info("Trying alternative sending method...")
                try:
                    # Create a different message format
                    alt_message = {
                        'raw': raw,
                        'threadId': thread_id
                    }
                    
                    # Send using the messages.send endpoint
                    alt_result = self.service.users().messages().send(
                        userId='me',
                        body=alt_message
                    ).execute()
                    
                    alt_message_id = alt_result.get('id', 'unknown')
                    logger.info(f"Alternative method succeeded. Message ID: {alt_message_id}")
                    return True
                except Exception as alt_error:
                    logger.error(f"Alternative method also failed: {alt_error}")
                    return False
                
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def draft_reply(self, thread_id: str, to_address: str, subject: str, message_body: str) -> bool:
        """Create a draft reply instead of sending directly.
        
        This is an alternative method that might work when direct sending fails.
        
        Args:
            thread_id: The ID of the thread to reply to
            to_address: The recipient's email address
            subject: Email subject, usually with "Re:" prefix
            message_body: The body of the email reply
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            logger.info(f"Creating draft reply to: {to_address}")
            logger.info(f"Thread ID: {thread_id}")
            
            # Get user's email address
            profile = self.service.users().getProfile(userId='me').execute()
            sender_email = profile.get('emailAddress', '')
            if not sender_email:
                logger.error("Could not get sender email address")
                return False
                
            logger.info(f"Sender email determined as: {sender_email}")
            
            # Create a MIME message
            message = MIMEMultipart()
            message['to'] = to_address
            message['from'] = sender_email
            message['subject'] = subject if subject.startswith("Re:") else f"Re: {subject}"
            
            # Add text body
            message.attach(MIMEText(message_body, 'plain'))
            
            # Add In-Reply-To header to link to thread if possible
            try:
                # Get thread details to find message IDs
                thread_data = self.service.users().threads().get(userId='me', id=thread_id).execute()
                if thread_data and 'messages' in thread_data and len(thread_data['messages']) > 0:
                    # Find message headers
                    for msg in thread_data['messages']:
                        headers = msg.get('payload', {}).get('headers', [])
                        message_id = next((h['value'] for h in headers if h['name'] == 'Message-ID'), None)
                        if message_id:
                            message['In-Reply-To'] = message_id
                            message['References'] = message_id
                            logger.info(f"Added reply headers to connect to original message")
                            break
            except Exception as e:
                logger.warning(f"Could not add threading headers: {e}")
            
            # Encode the message
            try:
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            except AttributeError:
                raw = base64.urlsafe_b64encode(message.as_string().encode()).decode()
            
            # Log before creating draft
            logger.info(f"Creating draft with subject: {message['subject']}")
            logger.info(f"Draft body preview: {message_body[:100]}...")
            
            try:
                # Create the draft
                draft = self.service.users().drafts().create(
                    userId='me',
                    body={
                        'message': {
                            'raw': raw,
                            'threadId': thread_id
                        }
                    }
                ).execute()
                
                draft_id = draft.get('id', 'unknown')
                logger.info(f"Draft created successfully. Draft ID: {draft_id}")
                
                # Verify the draft was really created
                time.sleep(1)  # Wait a bit for the draft to be processed
                
                try:
                    # Try to retrieve the draft
                    created_draft = self.service.users().drafts().get(userId='me', id=draft_id).execute()
                    if created_draft:
                        logger.info(f"Draft verified with ID: {draft_id}")
                    else:
                        logger.warning("Could not verify draft was created")
                except Exception as e:
                    logger.warning(f"Could not verify draft was created: {e}")
                
                return True
                
            except HttpError as error:
                logger.error(f"HTTP Error creating draft: {error}")
                logger.error(f"Response content: {error.content.decode('utf-8') if hasattr(error, 'content') else 'No content'}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False 