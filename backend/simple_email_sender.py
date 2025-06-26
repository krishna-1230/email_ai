"""
Simple email sender module that provides straightforward functions to send emails.
"""

import os
import logging
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger("simple_email_sender")

# Load environment variables
load_dotenv()

def send_simple_email(recipient_email, message_body, subject="Email from AI Assistant", sender_name="AI Email Assistant"):
    """
    Send a simple email to the specified recipient.
    Uses the SMTP configuration from environment variables.
    
    Args:
        recipient_email (str): The recipient's email address
        message_body (str): The message content
        subject (str, optional): Email subject line. Default is "Email from AI Assistant"
        sender_name (str, optional): Display name for the sender. Default is "AI Email Assistant"
        
    Returns:
        bool: True if successful, False if failed
    """
    # Get SMTP settings from environment variables
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_username = os.environ.get("SMTP_USERNAME", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    
    # Validate SMTP settings
    if not smtp_username or not smtp_password:
        logger.error("SMTP credentials not found. Set SMTP_USERNAME and SMTP_PASSWORD in .env file.")
        return False
    
    try:
        # Create message
        message = MIMEMultipart()
        message["To"] = recipient_email
        
        # Format the From header with display name
        message["From"] = formataddr((sender_name, smtp_username))
        message["Subject"] = subject
        
        # Attach message body
        message.attach(MIMEText(message_body, "plain"))
        
        # Connect to SMTP server and send
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls()  # Secure the connection
                server.login(smtp_username, smtp_password)
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
        except smtplib.SMTPException as smtp_err:
            logger.error(f"SMTP error: {smtp_err}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def send_reply_email(recipient_email, message_body, subject="Re: Email from AI Assistant", sender_name="AI Email Assistant"):
    """
    Send a reply email (adds Re: to subject if not already present).
    
    Args:
        recipient_email (str): The recipient's email address
        message_body (str): The message content
        subject (str, optional): Email subject line. Default is "Re: Email from AI Assistant"
        sender_name (str, optional): Display name for the sender. Default is "AI Email Assistant"
        
    Returns:
        bool: True if successful, False if failed
    """
    # Ensure subject has Re: prefix
    if subject and not subject.startswith("Re:"):
        subject = f"Re: {subject}"
    elif not subject:
        subject = "Re: (No Subject)"
    
    # Use the simple email function
    return send_simple_email(recipient_email, message_body, subject, sender_name)

def send_formal_reply(recipient_email, message_body, subject="Re: Email from AI Assistant"):
    """Convenience function to send a formal reply"""
    return send_reply_email(recipient_email, message_body, subject, "AI Assistant (Formal)")

def send_casual_reply(recipient_email, message_body, subject="Re: Email from AI Assistant"):
    """Convenience function to send a casual reply"""
    return send_reply_email(recipient_email, message_body, subject, "AI Assistant (Casual)")

def send_direct_reply(recipient_email, message_body, subject="Re: Email from AI Assistant"):
    """Convenience function to send a direct reply"""
    return send_reply_email(recipient_email, message_body, subject, "AI Assistant (Direct)") 