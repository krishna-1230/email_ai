import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
import logging
import streamlit as st
from backend.scheduler import MeetingScheduler

logger = logging.getLogger(__name__)

class CalendarManager:
    def __init__(self, meeting_scheduler: MeetingScheduler):
        """
        Initialize the calendar manager with a meeting scheduler.
        
        Args:
            meeting_scheduler: Instance of MeetingScheduler
        """
        self.meeting_scheduler = meeting_scheduler
        
    def get_upcoming_meetings(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get upcoming meetings from the calendar.
        
        Args:
            max_results: Maximum number of meetings to return
            
        Returns:
            List of upcoming meetings
        """
        try:
            return self.meeting_scheduler.get_upcoming_meetings(max_results)
        except Exception as e:
            logger.error(f"Error getting upcoming meetings: {e}")
            return []
    
    def render_calendar_management_ui(self):
        """Render the calendar management UI in Streamlit."""
        st.header("Calendar Management")
        
        # Create tabs for different calendar functions
        cal_tabs = st.tabs(["Upcoming Meetings", "Schedule Meeting", "Manage Meetings"])
        
        # Tab 1: Upcoming Meetings
        with cal_tabs[0]:
            st.subheader("Your Upcoming Meetings")
            
            with st.spinner("Loading your calendar..."):
                upcoming_meetings = self.get_upcoming_meetings(max_results=15)
                
                if not upcoming_meetings:
                    st.info("No upcoming meetings found on your calendar.")
                else:
                    # Display each meeting as an expandable item
                    for i, meeting in enumerate(upcoming_meetings):
                        with st.expander(f"{meeting['summary']} - {meeting['start']}"):
                            st.write(f"**Time:** {meeting['start']} to {meeting['end']}")
                            
                            if meeting.get('location'):
                                st.write(f"**Location:** {meeting['location']}")
                            
                            if meeting.get('description'):
                                st.write("**Description:**")
                                st.write(meeting['description'])
                            
                            if meeting.get('attendees'):
                                attendees = [a.get('email', '') for a in meeting['attendees']]
                                st.write(f"**Attendees:** {', '.join(attendees)}")
                            
                            # Actions for this meeting
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Cancel Meeting", key=f"cancel_{i}"):
                                    with st.spinner("Cancelling meeting..."):
                                        success = self.meeting_scheduler.cancel_meeting(
                                            meeting['id'], 
                                            notify_attendees=True
                                        )
                                        if success:
                                            st.success("Meeting cancelled successfully!")
                                            st.button("Refresh", key=f"refresh_cancel_{i}", 
                                                      on_click=st.rerun)
                                        else:
                                            st.error("Failed to cancel meeting.")
                            
                            with col2:
                                if st.button("Edit Meeting", key=f"edit_{i}"):
                                    st.session_state.meeting_to_edit = meeting
                                    st.session_state.editing_meeting = True
            
            if st.button("Refresh Calendar", key="refresh_calendar"):
                st.rerun()
        
        # Tab 2: Schedule Meeting
        with cal_tabs[1]:
            st.subheader("Schedule a New Meeting")
            
            with st.form(key="schedule_meeting_form"):
                meeting_title = st.text_input("Meeting Title", key="new_meeting_title")
                meeting_desc = st.text_area("Meeting Description", key="new_meeting_desc")
                
                col1, col2 = st.columns(2)
                with col1:
                    meeting_date = st.date_input("Date", datetime.now() + timedelta(days=1))
                with col2:
                    meeting_time = st.time_input("Start Time", datetime.now().replace(hour=10, minute=0))
                
                duration_options = {"15 minutes": 15, "30 minutes": 30, "45 minutes": 45, 
                                   "1 hour": 60, "1.5 hours": 90, "2 hours": 120}
                duration = st.selectbox("Duration", options=list(duration_options.keys()), index=1)
                
                meeting_location = st.text_input("Location (optional)", key="new_meeting_location")
                meeting_attendees = st.text_input("Attendees (comma-separated emails)", key="new_meeting_attendees")
                
                submit_button = st.form_submit_button("Schedule Meeting")
                
                if submit_button:
                    if meeting_title and meeting_attendees:
                        # Process the form data
                        start_time = datetime.combine(meeting_date, meeting_time)
                        duration_mins = duration_options[duration]
                        end_time = start_time + timedelta(minutes=duration_mins)
                        
                        attendee_list = [email.strip() for email in meeting_attendees.split(',')]
                        
                        with st.spinner("Scheduling meeting..."):
                            event = self.meeting_scheduler.schedule_meeting(
                                start_time,
                                end_time,
                                attendee_list,
                                meeting_title,
                                meeting_desc,
                                meeting_location
                            )
                            
                            if event:
                                st.success("Meeting scheduled successfully!")
                                # Link to the Google Calendar event
                                event_id = event['id']
                                cal_url = f"https://calendar.google.com/calendar/event?eid={event_id}"
                                st.markdown(f"[View in Google Calendar]({cal_url})")
                            else:
                                st.error("Failed to schedule meeting.")
                    else:
                        st.warning("Please provide a title and at least one attendee.")
        
        # Tab 3: Manage Meetings
        with cal_tabs[2]:
            st.subheader("Find Available Meeting Times")
            
            col1, col2 = st.columns(2)
            with col1:
                days_ahead = st.slider("Look ahead (days)", min_value=1, max_value=14, value=7)
            with col2:
                duration_mins = st.selectbox(
                    "Meeting duration",
                    options=[15, 30, 45, 60, 90, 120],
                    index=1,
                    format_func=lambda x: f"{x} minutes"
                )
            
            if st.button("Find Available Slots"):
                with st.spinner("Finding available meeting times..."):
                    available_slots = self.meeting_scheduler.get_available_slots(
                        duration_minutes=duration_mins, 
                        days_ahead=days_ahead
                    )
                    
                    if available_slots:
                        st.success(f"Found {len(available_slots)} available slots")
                        
                        # Display available slots
                        for i, slot in enumerate(available_slots):
                            with st.expander(f"Option {i+1}: {slot['start']}"):
                                st.write(f"Duration: {slot['duration']}")
                                
                                if st.button("Use This Slot", key=f"slot_{i}"):
                                    st.session_state.selected_slot = slot
                                    st.session_state.scheduling_new_meeting = True
                    else:
                        st.warning("No available slots found in the specified timeframe.")
            
            # Handle editing existing meeting if selected
            if hasattr(st.session_state, 'editing_meeting') and st.session_state.editing_meeting:
                meeting = st.session_state.meeting_to_edit
                st.subheader(f"Edit Meeting: {meeting['summary']}")
                
                with st.form(key="edit_meeting_form"):
                    edit_title = st.text_input("Meeting Title", value=meeting['summary'])
                    edit_desc = st.text_area("Meeting Description", value=meeting.get('description', ''))
                    
                    # Parse dates
                    try:
                        start_dt = datetime.strptime(meeting['start'], "%Y-%m-%d %I:%M %p")
                        edit_date = start_dt.date()
                        edit_time = start_dt.time()
                    except:
                        edit_date = datetime.now().date()
                        edit_time = datetime.now().time()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        new_date = st.date_input("Date", edit_date)
                    with col2:
                        new_time = st.time_input("Start Time", edit_time)
                    
                    duration_options = {"15 minutes": 15, "30 minutes": 30, "45 minutes": 45, 
                                       "1 hour": 60, "1.5 hours": 90, "2 hours": 120}
                    selected_duration = "30 minutes"  # Default
                    
                    try:
                        end_dt = datetime.strptime(meeting['end'], "%Y-%m-%d %I:%M %p")
                        duration_mins = int((end_dt - start_dt).total_seconds() / 60)
                        for label, mins in duration_options.items():
                            if mins == duration_mins:
                                selected_duration = label
                                break
                    except:
                        pass
                    
                    new_duration = st.selectbox("Duration", options=list(duration_options.keys()), 
                                             index=list(duration_options.keys()).index(selected_duration))
                    
                    new_location = st.text_input("Location (optional)", 
                                              value=meeting.get('location', ''))
                    
                    # Prepare attendees string
                    attendee_emails = []
                    if meeting.get('attendees'):
                        for attendee in meeting['attendees']:
                            if 'email' in attendee:
                                attendee_emails.append(attendee['email'])
                    
                    new_attendees = st.text_input("Attendees (comma-separated emails)", 
                                               value=', '.join(attendee_emails))
                    
                    update_button = st.form_submit_button("Update Meeting")
                    cancel_button = st.form_submit_button("Cancel")
                    
                    if cancel_button:
                        st.session_state.editing_meeting = False
                        st.rerun()
                    
                    if update_button:
                        if edit_title:
                            # Process the form data
                            start_time = datetime.combine(new_date, new_time)
                            duration_mins = duration_options[new_duration]
                            end_time = start_time + timedelta(minutes=duration_mins)
                            
                            attendee_list = [email.strip() for email in new_attendees.split(',')]
                            
                            with st.spinner("Updating meeting..."):
                                updated_event = self.meeting_scheduler.update_meeting(
                                    meeting['id'],
                                    start_time=start_time,
                                    end_time=end_time,
                                    attendees=attendee_list,
                                    summary=edit_title,
                                    description=edit_desc,
                                    location=new_location
                                )
                                
                                if updated_event:
                                    st.success("Meeting updated successfully!")
                                    st.session_state.editing_meeting = False
                                    st.button("Return to Calendar", on_click=st.rerun)
                                else:
                                    st.error("Failed to update meeting.")
                        else:
                            st.warning("Please provide a meeting title.") 