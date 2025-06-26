import streamlit as st
import os
import datetime
import traceback
import logging
from pathlib import Path
from dotenv import load_dotenv
from backend.email_reader import EmailReader
from backend.context_analyzer import ContextAnalyzer
from backend.reply_generator import ReplyGenerator
from backend.scheduler import MeetingScheduler
from backend.translator import EmailTranslator
from backend.simple_email_sender import send_reply_email
from backend.calendar_manager import CalendarManager
from utils.auth import check_credentials, revoke_credentials, get_gmail_service
from utils.config import get_config

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Email Assistant",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'selected_reply' not in st.session_state:
    st.session_state.selected_reply = None
if 'selected_tone' not in st.session_state:
    st.session_state.selected_tone = None
if 'meeting_details_open' not in st.session_state:
    st.session_state.meeting_details_open = False
if 'reply_just_sent' not in st.session_state:
    st.session_state.reply_just_sent = False
if 'recipient_email' not in st.session_state:
    st.session_state.recipient_email = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = "email"
if 'editing_meeting' not in st.session_state:
    st.session_state.editing_meeting = False
if 'scheduling_new_meeting' not in st.session_state:
    st.session_state.scheduling_new_meeting = False

# Load and validate configuration
try:
    config = get_config()
except ValueError as e:
    st.error(f"Configuration Error: {str(e)}")
    st.info("Please set up the required environment variables in the .env file.")
    st.stop()

# Initialize components
try:
    gmail_service, gmail_creds = get_gmail_service()
    email_reader = EmailReader(gmail_service)
    
    # Check if we have send permission
    if not getattr(email_reader, 'can_send', True):
        st.warning("⚠️ Your Gmail authorization is missing send permission. You won't be able to send replies.")
        if st.button("Reauthorize with Send Permission"):
            # Delete the token file to force reauthorization
            token_path = Path('token.pickle')
            if token_path.exists():
                token_path.unlink()
            st.success("Token deleted. Please refresh the page to reauthorize.")
            st.button("Refresh Now", on_click=st.rerun)
    
    context_analyzer = ContextAnalyzer()
    reply_generator = ReplyGenerator()
    meeting_scheduler = MeetingScheduler(gmail_creds)
    calendar_manager = CalendarManager(meeting_scheduler)
    email_translator = EmailTranslator()
except Exception as e:
    st.error(f"Initialization Error: {str(e)}")
    st.info("Please check your API keys and credentials.")
    st.stop()

def main():
    # Initialize session state for various app features
    if 'threads' not in st.session_state:
        st.session_state.threads = []
    if 'selected_thread' not in st.session_state:
        st.session_state.selected_thread = None
    if 'thread_index' not in st.session_state:
        st.session_state.thread_index = -1
    if 'translated_messages' not in st.session_state:
        st.session_state.translated_messages = {}
    if 'detected_languages' not in st.session_state:
        st.session_state.detected_languages = {}
    if 'meeting_details_open' not in st.session_state:
        st.session_state.meeting_details_open = False
        
    # Email sending state variables
    if 'reply_just_sent' not in st.session_state:
        st.session_state.reply_just_sent = False
    if 'reply_method' not in st.session_state:
        st.session_state.reply_method = None
    if 'recipient_email' not in st.session_state:
        st.session_state.recipient_email = None
    if 'message_confirmed' not in st.session_state:
        st.session_state.message_confirmed = False
    
    st.title("AI-Powered Email Assistant")
    
    # Check authentication
    if not check_credentials():
        st.warning("Please authenticate with Gmail to continue.")
        if st.button("Authenticate"):
            try:
                EmailReader()  # This will trigger the OAuth flow
                st.rerun()
            except Exception as e:
                st.error(f"Authentication Error: {str(e)}")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        # View selector
        st.subheader("Navigation")
        view_options = {
            "email": "📧 Email Management", 
            "calendar": "📅 Calendar Management"
        }
        selected_view = st.radio(
            "Select View",
            options=list(view_options.keys()),
            format_func=lambda x: view_options[x],
            index=0 if st.session_state.current_view == "email" else 1
        )
        st.session_state.current_view = selected_view
        
        # Email settings
        st.subheader("Email Settings")
        smtp_username = os.environ.get("SMTP_USERNAME")
        smtp_password = os.environ.get("SMTP_PASSWORD")
        if smtp_username and smtp_password:
            st.success(f"✅ SMTP configured for: {smtp_username}")
        else:
            st.warning("⚠️ SMTP not configured. Set SMTP_USERNAME and SMTP_PASSWORD in .env file.")
        
        # Language selection
        st.subheader("Translation")
        languages = email_translator.get_supported_languages()
        target_language = st.selectbox(
            "Target Language",
            options=[lang['code'] for lang in languages],
            format_func=lambda x: next(lang['name'] for lang in languages if lang['code'] == x),
            index=[lang['code'] for lang in languages].index(config.get('DEFAULT_TARGET_LANGUAGE', 'en'))
        )
        
        # Debug information (only shown if DEBUG is True)
        if config.get('DEBUG', 'False').lower() == 'true':
            st.subheader("Debug Info")
            st.json(config)
        
        if st.button("Logout"):
            revoke_credentials()
            st.rerun()

        # Send Reply section (renamed from Debug Tools)
        st.subheader("Send Reply")
        with st.form("send_reply_form"):
            test_email = st.text_input("Recipient email")
            test_message = st.text_area("Message", "This is a message from the AI Email Assistant.")
            test_subject = st.text_input("Subject", "Email from AI Assistant")
            test_submit = st.form_submit_button("Send Email")
            
            if test_submit and test_email:
                with st.spinner("Sending email..."):
                    try:
                        success = send_reply_email(
                            recipient_email=test_email,
                            message_body=test_message,
                            subject=test_subject,
                            sender_name="AI Email Assistant"
                        )
                        
                        if success:
                            st.success(f"✅ Email sent to {test_email}")
                        else:
                            st.error("❌ Email failed to send")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    # Main content - Show either Email Management or Calendar Management based on selected view
    if st.session_state.current_view == "email":
        render_email_management()
    else:
        calendar_manager.render_calendar_management_ui()

def render_email_management():
    """Render the email management interface."""
    st.header("Email Management")
    
    # Fetch and display email threads
    with st.spinner("Fetching email threads..."):
        try:
            threads = email_reader.get_threads(max_results=int(config.get('MAX_THREADS_TO_FETCH', 10)))
        except Exception as e:
            st.error(f"Error fetching email threads: {str(e)}")
            st.info("Please check your Gmail API credentials.")
            return
    
    if not threads:
        st.info("No email threads found.")
        return

    # Thread selection
    thread_options = {
        f"{thread['messages'][-1]['subject']} - {thread['messages'][-1]['sender']}": thread
        for thread in threads
    }
    
    selected_thread = st.selectbox(
        "Select an email thread",
        options=list(thread_options.keys())
    )
    
    if selected_thread:
        thread = thread_options[selected_thread]
        
        # Display thread content
        st.subheader("Thread Content")
        for message in reversed(thread['messages']):
            with st.expander(f"From: {message['sender']} - {message['date']}"):
                st.write(f"**Subject:** {message['subject']}")
                st.write(message['body'])
                
                # Translation button
                if st.button("Translate", key=f"translate_{message['id']}"):
                    with st.spinner("Translating..."):
                        try:
                            translated = email_translator.translate_email(message, target_language)
                            st.write("---")
                            st.write("**Translation:**")
                            st.write(translated['body'])
                        except Exception as e:
                            st.error(f"Translation Error: {str(e)}")
        
        # Analyze thread
        if st.button("Analyze Thread"):
            with st.spinner("Analyzing thread..."):
                try:
                    analysis = context_analyzer.analyze_thread(thread)
                    
                    if analysis:
                        # Display analysis
                        st.subheader("Thread Analysis")
                        st.write(analysis['thread_analysis'])
                        
                        # Display sentiment and urgency
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Sentiment", analysis['sentiment']['sentiment'])
                        with col2:
                            st.metric("Urgency", analysis['urgency'])
                        
                        # Display key points
                        st.subheader("Key Points")
                        for point in analysis['key_points']:
                            st.write(f"- {point}")
                        
                        # Check for meeting requests
                        latest_message = thread['messages'][-1]
                        meeting_requests = meeting_scheduler.extract_meeting_requests(latest_message['body'])
                        
                        if meeting_requests:
                            st.subheader("Meeting Suggestions")
                            try:
                                suggestions = meeting_scheduler.suggest_meeting_times(
                                    latest_message['body'],
                                    duration_minutes=int(config.get('MEETING_DURATION_MINUTES', 30)),
                                    days_ahead=int(config.get('DAYS_AHEAD_FOR_SCHEDULING', 7))
                                )
                                
                                if suggestions:
                                    for i, slot in enumerate(suggestions, 1):
                                        slot_key = f"slot_{i}"
                                        with st.expander(f"Option {i}: {slot['start']}"):
                                            st.write(f"Duration: {slot['duration']}")
                                            
                                            if st.button("Schedule Meeting", key=f"schedule_{i}"):
                                                st.session_state.meeting_details_open = True
                                                st.session_state.current_slot = slot
                                                st.session_state.current_slot_key = slot_key
                                    
                                    # Meeting details form
                                    if st.session_state.meeting_details_open:
                                        slot = st.session_state.current_slot
                                        st.subheader("Meeting Details")
                                        
                                        with st.form(key="meeting_form"):
                                            summary = st.text_input("Meeting Title", key="meeting_title")
                                            description = st.text_area("Description", key="meeting_desc")
                                            attendees = st.text_input("Attendees (comma-separated emails)", key="meeting_attendees")
                                            
                                            submit_button = st.form_submit_button("Schedule Meeting")
                                            
                                            if submit_button:
                                                if summary and attendees:
                                                    attendee_list = [email.strip() for email in attendees.split(',')]
                                                    
                                                    # Convert string times to datetime objects
                                                    start_time = datetime.datetime.strptime(slot['start'], "%Y-%m-%d %I:%M %p")
                                                    end_time = datetime.datetime.strptime(slot['end'], "%Y-%m-%d %I:%M %p")
                                                    
                                                    event = meeting_scheduler.schedule_meeting(
                                                        start_time,
                                                        end_time,
                                                        attendee_list,
                                                        summary,
                                                        description
                                                    )
                                                    
                                                    if event:
                                                        st.success("Meeting scheduled successfully!")
                                                        st.session_state.meeting_details_open = False
                                                    else:
                                                        st.error("Failed to schedule meeting.")
                                                else:
                                                    st.warning("Please provide a title and attendees.")
                            except Exception as e:
                                st.error(f"Meeting Scheduling Error: {str(e)}")
                                st.info("Please check your Google Calendar API credentials.")
                        
                        # Generate replies
                        st.subheader("Suggested Replies")
                        try:
                            replies = reply_generator.generate_replies(analysis)
                            
                            # Display replies in tabs
                            tabs = st.tabs(["Formal", "Casual", "Direct"])
                            
                            # Get sender information for reply
                            latest_message = thread['messages'][-1]
                            
                            # Extract the sender's email address from the latest message
                            original_sender = latest_message['sender']
                            
                            # Parse the email address from the sender field which might be in format "Name <email@example.com>"
                            if '<' in original_sender and '>' in original_sender:
                                reply_to_email = original_sender.split('<')[1].split('>')[0].strip()
                            else:
                                reply_to_email = original_sender.strip()
                            
                            # Ensure we have a valid email address
                            if not reply_to_email or reply_to_email.strip() == '':
                                # If we can't extract a valid email, use the user's own email
                                profile = email_reader.service.users().getProfile(userId='me').execute()
                                reply_to_email = profile.get('emailAddress', '')
                            
                            # Show the recipient email in the UI for verification
                            st.info(f"**Reply will be sent to:** {reply_to_email}")
                            
                            # Get subject from the latest message
                            subject = latest_message['subject']
                            
                            for tab, (tone, reply) in zip(tabs, replies.items()):
                                with tab:
                                    st.write(reply)
                                    if st.button(f"Use {tone.title()} Reply", key=f"use_{tone}"):
                                        # Store the reply in session state
                                        st.session_state.selected_reply = reply
                                        st.session_state.selected_tone = tone
                                        
                                        # Send the reply immediately using our simple function
                                        with st.spinner(f"Sending {tone} reply..."):
                                            # Add Re: to subject if not already present
                                            if not subject.startswith("Re:"):
                                                email_subject = f"Re: {subject}"
                                            else:
                                                email_subject = subject
                                                
                                            # Determine sender name based on tone
                                            sender_name = f"AI Assistant ({tone.title()})"
                                            
                                            # Use the simple_email_sender function
                                            try:
                                                success = send_reply_email(
                                                    recipient_email=reply_to_email,
                                                    message_body=reply,
                                                    subject=email_subject,
                                                    sender_name=sender_name
                                                )
                                                
                                                if success:
                                                    # Update session state
                                                    st.session_state.reply_just_sent = True
                                                    st.session_state.reply_method = "SMTP_DIRECT"
                                                    st.session_state.recipient_email = reply_to_email
                                                    
                                                    # Show success message to user
                                                    st.success(f"""
                                                    ✅ {tone.title()} reply sent successfully to {reply_to_email}!
                                                    
                                                    **Subject:** {subject}
                                                    
                                                    ℹ️ **Important Notes:**
                                                    1. Emails may take a few minutes to appear in recipients' inboxes
                                                    2. Check your sent folder to confirm delivery
                                                    """)
                                                    
                                                    # Refresh button
                                                    if st.button("Refresh", key=f"refresh_{tone}"):
                                                        st.rerun()
                                                        
                                                else:
                                                    # Show error message
                                                    st.error(f"""
                                                    ❌ Failed to send {tone} reply.
                                                    
                                                    Please check the logs for more information.
                                                    """)
                                                    
                                                    # Let user try again
                                                    if st.button("Try Again", key=f"retry_{tone}"):
                                                        st.rerun()
                                            except Exception as e:
                                                st.error(f"Error sending email: {str(e)}")
                            
                        except Exception as e:
                            st.error(f"Reply Generation Error: {str(e)}")
                except Exception as e:
                    st.error(f"Analysis Error: {str(e)}")
                    st.info("Please check your Gemini API key.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application Error: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"Application Error: {str(e)}")
        st.code(traceback.format_exc()) 