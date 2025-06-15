import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import pytz
import re

load_dotenv()

class MeetingScheduler:
    def __init__(self, credentials):
        """Initialize the meeting scheduler with Gmail credentials."""
        self.service = build('calendar', 'v3', credentials=credentials)
    
    def extract_meeting_requests(self, email_body: str) -> List[Dict[str, Any]]:
        """
        Extract potential meeting requests from email body.
        
        Args:
            email_body: The content of the email
            
        Returns:
            List of potential meeting requests
        """
        meeting_requests = []
        
        # Common meeting request patterns
        patterns = [
            r"(?i)schedule.*meeting",
            r"(?i)set up.*call",
            r"(?i)book.*time",
            r"(?i)find.*slot",
            r"(?i)available.*time"
        ]
        
        # Check for patterns
        for pattern in patterns:
            if re.search(pattern, email_body):
                # Extract potential date/time mentions
                date_matches = re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', email_body)
                time_matches = re.findall(r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b', email_body)
                
                meeting_requests.append({
                    'type': 'meeting_request',
                    'dates': date_matches,
                    'times': time_matches,
                    'context': email_body
                })
        
        return meeting_requests
    
    def get_available_slots(self, duration_minutes: int = 30, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get available time slots for scheduling."""
        try:
            # Get calendar events for the next week
            now = datetime.utcnow()
            end_time = now + timedelta(days=days_ahead)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Get business hours (9 AM to 5 PM)
            business_hours = []
            current_date = now.date()
            
            for _ in range(days_ahead):
                if current_date.weekday() < 5:  # Monday to Friday
                    start_time = datetime.combine(current_date, datetime.min.time().replace(hour=9))
                    end_time = datetime.combine(current_date, datetime.min.time().replace(hour=17))
                    business_hours.append((start_time, end_time))
                current_date += timedelta(days=1)
            
            # Find available slots
            available_slots = []
            
            for start, end in business_hours:
                current = start
                while current + timedelta(minutes=duration_minutes) <= end:
                    slot_available = True
                    
                    # Check if slot overlaps with any event
                    for event in events:
                        event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                        event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))
                        
                        if (current < event_end and 
                            current + timedelta(minutes=duration_minutes) > event_start):
                            slot_available = False
                            break
                    
                    if slot_available:
                        available_slots.append({
                            'start': current.isoformat(),
                            'end': (current + timedelta(minutes=duration_minutes)).isoformat()
                        })
                    
                    current += timedelta(minutes=30)  # Check every 30 minutes
            
            return available_slots
        
        except Exception as e:
            print(f"Error getting available slots: {e}")
            return []
    
    def suggest_meeting_times(
        self,
        email_body: str,
        duration_minutes: int = 30,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Suggest meeting times based on email content and calendar availability.
        
        Args:
            email_body: The content of the email
            duration_minutes: Duration of the meeting in minutes
            days_ahead: Number of days to look ahead for availability
            
        Returns:
            List of suggested meeting time slots
        """
        meeting_requests = self.extract_meeting_requests(email_body)
        
        if not meeting_requests:
            return []
        
        # Get available slots
        available_slots = self.get_available_slots(duration_minutes, days_ahead)
        
        # Format suggestions
        suggestions = []
        for slot in available_slots[:3]:  # Suggest top 3 slots
            start_time = datetime.fromisoformat(slot['start'])
            end_time = datetime.fromisoformat(slot['end'])
            
            suggestions.append({
                'start': start_time.strftime("%Y-%m-%d %I:%M %p"),
                'end': end_time.strftime("%Y-%m-%d %I:%M %p"),
                'duration': f"{duration_minutes} minutes"
            })
        
        return suggestions
    
    def schedule_meeting(
        self,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        summary: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Schedule a meeting in Google Calendar.
        
        Args:
            start_time: Start time of the meeting
            end_time: End time of the meeting
            attendees: List of attendee email addresses
            summary: Meeting title
            description: Meeting description
            
        Returns:
            Created calendar event
        """
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [{'email': email} for email in attendees],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()
            return event
        except Exception as e:
            print(f"Error scheduling meeting: {e}")
            return None 