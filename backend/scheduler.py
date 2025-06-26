import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import pytz
import re
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class MeetingScheduler:
    def __init__(self, credentials):
        """Initialize the meeting scheduler with Gmail credentials."""
        self.service = build('calendar', 'v3', credentials=credentials)
        self.timezone = os.getenv('TIMEZONE', 'UTC')
    
    def extract_meeting_requests(self, email_body: str) -> List[Dict[str, Any]]:
        """
        Extract potential meeting requests from email body.
        
        Args:
            email_body: The content of the email
            
        Returns:
            List of potential meeting requests
        """
        if not email_body or not isinstance(email_body, str):
            logger.warning("Invalid email body provided")
            return []
            
        meeting_requests = []
        
        # Common meeting request patterns
        patterns = [
            r"(?i)schedule.*meeting",
            r"(?i)set up.*call",
            r"(?i)book.*time",
            r"(?i)find.*slot",
            r"(?i)available.*time",
            r"(?i)like to meet",
            r"(?i)discuss.*in person",
            r"(?i)let's meet",
            r"(?i)can we meet",
            r"(?i)meeting request"
        ]
        
        # Check for patterns
        for pattern in patterns:
            if re.search(pattern, email_body):
                # Extract potential date/time mentions
                date_matches = re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', email_body)
                time_matches = re.findall(r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b', email_body)
                weekday_matches = re.findall(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b', email_body, re.IGNORECASE)
                
                meeting_requests.append({
                    'type': 'meeting_request',
                    'dates': date_matches,
                    'times': time_matches,
                    'weekdays': weekday_matches,
                    'context': email_body
                })
        
        return meeting_requests
    
    def get_user_timezone(self) -> str:
        """Get the user's calendar timezone setting."""
        try:
            settings = self.service.settings().get(setting='timezone').execute()
            return settings['value']
        except Exception as e:
            logger.error(f"Error getting user timezone: {e}")
            return self.timezone
    
    def get_available_slots(self, start_date: Optional[datetime] = None, 
                          duration_minutes: int = 30, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get available time slots for scheduling."""
        try:
            # Input validation
            if duration_minutes < 15:
                logger.warning(f"Duration too short: {duration_minutes} minutes, using 15 minutes")
                duration_minutes = 15
            elif duration_minutes > 480:  # 8 hours
                logger.warning(f"Duration too long: {duration_minutes} minutes, using 480 minutes")
                duration_minutes = 480
                
            if days_ahead < 1:
                logger.warning(f"Days ahead too few: {days_ahead}, using 1 day")
                days_ahead = 1
            elif days_ahead > 60:  # 2 months
                logger.warning(f"Days ahead too many: {days_ahead}, using 60 days")
                days_ahead = 60
            
            # Get the user's timezone
            user_tz = pytz.timezone(self.get_user_timezone())
            
            # Set start date to now if not provided
            if not start_date:
                now = datetime.now(user_tz)
                # Round to the next 30 minutes
                minutes_to_add = 30 - (now.minute % 30)
                if minutes_to_add == 30:
                    minutes_to_add = 0
                now = now + timedelta(minutes=minutes_to_add)
                start_date = now.replace(second=0, microsecond=0)
            else:
                # Ensure the start date has timezone info
                if start_date.tzinfo is None:
                    start_date = user_tz.localize(start_date)
            
            end_date = start_date + timedelta(days=days_ahead)
            
            # Format times for API
            time_min = start_date.isoformat()
            time_max = end_date.isoformat()
            
            # Get busy times from primary calendar
            freebusy_query = {
                'timeMin': time_min,
                'timeMax': time_max,
                'items': [{'id': 'primary'}]
            }
            
            freebusy_response = self.service.freebusy().query(body=freebusy_query).execute()
            busy_slots = freebusy_response['calendars']['primary'].get('busy', [])
            
            # Get business hours (9 AM to 5 PM, Monday to Friday)
            business_hours = []
            current_date = start_date.date()
            
            for _ in range(days_ahead):
                if current_date.weekday() < 5:  # Monday to Friday
                    day_start = datetime.combine(current_date, datetime.min.time().replace(hour=9))
                    day_start = user_tz.localize(day_start)
                    day_end = datetime.combine(current_date, datetime.min.time().replace(hour=17))
                    day_end = user_tz.localize(day_end)
                    business_hours.append((day_start, day_end))
                current_date += timedelta(days=1)
            
            # Find available slots within business hours
            available_slots = []
            slot_duration = timedelta(minutes=duration_minutes)
            
            for start, end in business_hours:
                current = start
                while current + slot_duration <= end:
                    slot_available = True
                    
                    # Check if slot overlaps with any busy time
                    for busy in busy_slots:
                        try:
                            busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                            busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                            
                            # Convert to user timezone for comparison
                            busy_start = busy_start.astimezone(user_tz)
                            busy_end = busy_end.astimezone(user_tz)
                            
                            if current < busy_end and current + slot_duration > busy_start:
                                slot_available = False
                                break
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Error processing busy slot: {e}")
                            continue
                    
                    if slot_available:
                        slot_end = current + slot_duration
                        available_slots.append({
                            'start': current.strftime("%Y-%m-%d %I:%M %p"),
                            'end': slot_end.strftime("%Y-%m-%d %I:%M %p"),
                            'duration': f"{duration_minutes} minutes"
                        })
                    
                    # Move to next slot (30 minute increments)
                    current += timedelta(minutes=30)
            
            # Return maximum 10 available slots
            return available_slots[:10]
        
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
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
        if not email_body:
            logger.warning("Empty email body provided")
            return []
            
        meeting_requests = self.extract_meeting_requests(email_body)
        
        if not meeting_requests:
            return []
        
        # Try to extract date preferences from the email
        start_date = None
        for request in meeting_requests:
            if request['dates']:
                # Try to parse dates mentioned in the email
                for date_str in request['dates']:
                    try:
                        # Handle different date formats
                        if '-' in date_str:
                            parts = date_str.split('-')
                        elif '/' in date_str:
                            parts = date_str.split('/')
                        else:
                            continue
                            
                        if len(parts) == 3:
                            # Check if month/day are in correct positions (assuming MM/DD/YYYY format)
                            month, day = int(parts[0]), int(parts[1])
                            
                            # Basic validation
                            if month < 1 or month > 12 or day < 1 or day > 31:
                                logger.warning(f"Invalid date components in {date_str}: month={month}, day={day}")
                                continue
                                
                            # Handle 2-digit year
                            year = parts[2]
                            if len(year) == 2:
                                year = f"20{year}"
                            
                            try:
                                extracted_date = datetime(int(year), month, day)
                                
                                # Only use dates in the future
                                if extracted_date.date() >= datetime.now().date():
                                    start_date = extracted_date
                                    logger.info(f"Found valid date in email: {start_date}")
                                    break
                                else:
                                    logger.info(f"Ignoring past date: {extracted_date}")
                            except ValueError as e:
                                logger.warning(f"Invalid date {date_str}: {e}")
                                continue
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing date {date_str}: {e}")
                        continue
        
        # Get available slots starting from the extracted date or now
        available_slots = self.get_available_slots(start_date, duration_minutes, days_ahead)
        
        # Format suggestions
        if available_slots:
            return available_slots
        else:
            # If no slots available in requested timeframe, get default slots
            logger.info("No slots available for the requested date, using default time range")
            return self.get_available_slots(None, duration_minutes, days_ahead)
    
    def schedule_meeting(
        self,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        summary: str,
        description: str = "",
        location: str = "",
        send_invites: bool = True
    ) -> Dict[str, Any]:
        """
        Schedule a meeting in Google Calendar.
        
        Args:
            start_time: Start time of the meeting
            end_time: End time of the meeting
            attendees: List of attendee email addresses
            summary: Meeting title
            description: Meeting description
            location: Meeting location
            send_invites: Whether to send invitation emails
            
        Returns:
            Created calendar event
        """
        if not start_time or not end_time or not attendees or not summary:
            logger.error("Missing required parameters for scheduling meeting")
            return None
            
        # Validate email addresses
        valid_attendees = []
        for email in attendees:
            # Basic email validation
            if '@' in email and '.' in email.split('@')[1]:
                valid_attendees.append(email)
            else:
                logger.warning(f"Invalid email address: {email}")
        
        if not valid_attendees:
            logger.error("No valid attendee email addresses provided")
            return None
            
        # Get user timezone
        user_tz = self.get_user_timezone()
        
        # Ensure datetime objects have timezone info
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=pytz.timezone(user_tz))
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=pytz.timezone(user_tz))
            
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': user_tz,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': user_tz,
            },
            'attendees': [{'email': email} for email in valid_attendees],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        # Add location if provided
        if location:
            event['location'] = location
            
        try:
            send_updates = 'all' if send_invites else 'none'
            event = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates=send_updates
            ).execute()
            logger.info(f"Meeting scheduled: {summary} on {start_time}")
            return event
        except Exception as e:
            logger.error(f"Error scheduling meeting: {e}")
            return None
    
    def get_upcoming_meetings(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get a list of upcoming meetings from the user's calendar.
        
        Args:
            max_results: Maximum number of events to return
            
        Returns:
            List of upcoming calendar events
        """
        try:
            # Validate max_results
            if max_results < 1:
                max_results = 1
            elif max_results > 100:
                max_results = 100
                
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events for display
            formatted_events = []
            for event in events:
                start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'Unknown'))
                end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date', 'Unknown'))
                
                # Convert to datetime objects if possible
                try:
                    if 'T' in start:  # This is a dateTime string
                        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        start = start_dt.strftime("%Y-%m-%d %I:%M %p")
                except Exception as e:
                    logger.warning(f"Error parsing start time: {e}")
                    
                try:
                    if 'T' in end:  # This is a dateTime string
                        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                        end = end_dt.strftime("%Y-%m-%d %I:%M %p")
                except Exception as e:
                    logger.warning(f"Error parsing end time: {e}")
                
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start': start,
                    'end': end,
                    'attendees': event.get('attendees', []),
                    'location': event.get('location', ''),
                    'description': event.get('description', '')
                })
                
            return formatted_events
            
        except Exception as e:
            logger.error(f"Error retrieving upcoming meetings: {e}")
            return []
    
    def update_meeting(
        self,
        event_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        attendees: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        send_updates: bool = True
    ) -> Dict[str, Any]:
        """
        Update an existing meeting in Google Calendar.
        
        Args:
            event_id: The ID of the event to update
            start_time: New start time (optional)
            end_time: New end time (optional)
            attendees: New list of attendee emails (optional)
            summary: New meeting title (optional)
            description: New meeting description (optional)
            location: New meeting location (optional)
            send_updates: Whether to send update emails
            
        Returns:
            Updated calendar event
        """
        if not event_id:
            logger.error("No event ID provided for updating")
            return None
            
        try:
            # Get the existing event
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update fields if provided
            if summary:
                event['summary'] = summary
            if description is not None:  # Allow empty descriptions
                event['description'] = description
            if location is not None:  # Allow empty locations
                event['location'] = location
                
            user_tz = self.get_user_timezone()
                
            if start_time:
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=pytz.timezone(user_tz))
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': user_tz
                }
                
            if end_time:
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=pytz.timezone(user_tz))
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': user_tz
                }
                
            if attendees:
                # Validate email addresses
                valid_attendees = []
                for email in attendees:
                    # Basic email validation
                    if '@' in email and '.' in email.split('@')[1]:
                        valid_attendees.append(email)
                    else:
                        logger.warning(f"Invalid email address: {email}")
                
                if valid_attendees:
                    event['attendees'] = [{'email': email} for email in valid_attendees]
            
            # Update the event
            send_updates_value = 'all' if send_updates else 'none'
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates=send_updates_value
            ).execute()
            
            logger.info(f"Meeting updated: {updated_event.get('summary')}")
            return updated_event
            
        except Exception as e:
            logger.error(f"Error updating meeting: {e}")
            return None
    
    def cancel_meeting(self, event_id: str, notify_attendees: bool = True) -> bool:
        """
        Cancel a meeting in Google Calendar.
        
        Args:
            event_id: The ID of the event to cancel
            notify_attendees: Whether to notify attendees about cancellation
            
        Returns:
            Boolean indicating success or failure
        """
        if not event_id:
            logger.error("No event ID provided for cancellation")
            return False
            
        try:
            # First verify the event exists
            try:
                self.service.events().get(calendarId='primary', eventId=event_id).execute()
            except Exception as e:
                logger.error(f"Event not found: {event_id} - {e}")
                return False
                
            # Proceed with deletion
            send_updates = 'all' if notify_attendees else 'none'
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates=send_updates
            ).execute()
            
            logger.info(f"Meeting cancelled: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling meeting: {e}")
            return False 