import streamlit as st
import os
from dotenv import load_dotenv
from backend.email_reader import EmailReader
from backend.context_analyzer import ContextAnalyzer
from backend.reply_generator import ReplyGenerator
from backend.scheduler import MeetingScheduler
from backend.translator import EmailTranslator
from utils.auth import check_credentials, revoke_credentials, get_gmail_service
from utils.config import get_config
import datetime
import traceback

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
    context_analyzer = ContextAnalyzer()
    reply_generator = ReplyGenerator()
    meeting_scheduler = MeetingScheduler(gmail_creds)
    email_translator = EmailTranslator()
except Exception as e:
    st.error(f"Initialization Error: {str(e)}")
    st.info("Please check your API keys and credentials.")
    st.stop()

def main():
    st.title("AI-Powered Email Assistant")
    
    # Check authentication
    if not check_credentials():
        st.warning("Please authenticate with Gmail to continue.")
        if st.button("Authenticate"):
            try:
                EmailReader()  # This will trigger the OAuth flow
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Authentication Error: {str(e)}")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
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
            st.experimental_rerun()
    
    # Main content
    st.header("Email Threads")
    
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
                            for tab, (tone, reply) in zip(tabs, replies.items()):
                                with tab:
                                    st.write(reply)
                                    if st.button(f"Use {tone.title()} Reply", key=f"use_{tone}"):
                                        st.session_state.selected_reply = reply
                                        st.session_state.selected_tone = tone
                            
                            # Display selected reply
                            if 'selected_reply' in st.session_state and st.session_state.selected_reply:
                                st.subheader(f"Selected Reply ({st.session_state.selected_tone})")
                                st.write(st.session_state.selected_reply)
                                
                                # Add feedback buttons
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("👍 Good Reply"):
                                        st.success("Thank you for your feedback!")
                                with col2:
                                    if st.button("👎 Needs Improvement"):
                                        st.info("We'll use your feedback to improve our suggestions.")
                        except Exception as e:
                            st.error(f"Reply Generation Error: {str(e)}")
                except Exception as e:
                    st.error(f"Analysis Error: {str(e)}")
                    st.info("Please check your Gemini API key.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.code(traceback.format_exc()) 