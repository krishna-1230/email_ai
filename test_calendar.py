"""
Test script for calendar functionality.
Run this script to test calendar integration directly.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from backend.scheduler import MeetingScheduler
from utils.auth import get_gmail_service

# Load environment variables
load_dotenv()

def test_calendar_features():
    print("Testing Calendar Features")
    print("-" * 50)
    
    # Get gmail service and credentials
    try:
        gmail_service, gmail_creds = get_gmail_service()
        print("✓ Successfully authenticated with Gmail API")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return
    
    # Initialize scheduler
    try:
        scheduler = MeetingScheduler(gmail_creds)
        print("✓ Meeting scheduler initialized")
    except Exception as e:
        print(f"✗ Failed to initialize meeting scheduler: {e}")
        return
    
    # Test getting upcoming meetings
    try:
        upcoming_meetings = scheduler.get_upcoming_meetings(max_results=5)
        print(f"✓ Found {len(upcoming_meetings)} upcoming meetings")
        
        if upcoming_meetings:
            print("\nUpcoming meetings:")
            for meeting in upcoming_meetings:
                print(f"- {meeting['summary']} ({meeting['start']})")
    except Exception as e:
        print(f"✗ Failed to get upcoming meetings: {e}")
    
    # Test finding available slots
    try:
        print("\nFinding available meeting slots...")
        slots = scheduler.get_available_slots(days_ahead=3)
        print(f"✓ Found {len(slots)} available slots")
        
        if slots:
            print("\nAvailable slots:")
            for i, slot in enumerate(slots[:3]):  # Show first 3 slots
                print(f"- Option {i+1}: {slot['start']} ({slot['duration']})")
    except Exception as e:
        print(f"✗ Failed to find available slots: {e}")
    
    # Test scheduling a meeting (commented out to prevent accidental scheduling)
    """
    try:
        print("\nAttempting to schedule a test meeting...")
        # Schedule a meeting 1 day from now
        start_time = datetime.now() + timedelta(days=1)
        start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)
        
        # Get the user's own email for testing
        profile = gmail_service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress', '')
        
        if not user_email:
            print("✗ Could not get user email")
        else:
            event = scheduler.schedule_meeting(
                start_time,
                end_time,
                [user_email],  # Send invite to yourself for testing
                "Test Meeting - Please Ignore",
                "This is a test meeting created by the AI Email Assistant.",
                "Virtual Meeting"
            )
            
            if event:
                print(f"✓ Test meeting scheduled successfully! (ID: {event.get('id', 'unknown')})")
                
                # Cancel the test meeting to clean up
                print("Cancelling test meeting...")
                if scheduler.cancel_meeting(event['id'], notify_attendees=False):
                    print("✓ Test meeting cancelled successfully")
                else:
                    print("✗ Failed to cancel test meeting")
            else:
                print("✗ Failed to schedule test meeting")
    except Exception as e:
        print(f"✗ Error in meeting scheduling test: {e}")
    """
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_calendar_features() 