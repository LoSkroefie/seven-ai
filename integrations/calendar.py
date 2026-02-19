"""
Google Calendar integration
"""
import pickle
import os.path
from typing import Optional, Dict
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import config

class CalendarManager:
    """Manage Google Calendar events"""
    
    def __init__(self):
        self.creds = None
        self.service = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar
        
        Returns:
            True if successful, False otherwise
        """
        # Check for existing token
        if config.CALENDAR_TOKEN.exists():
            try:
                with open(config.CALENDAR_TOKEN, 'rb') as token:
                    self.creds = pickle.load(token)
            except Exception as e:
                print(f"[WARNING]  Error loading calendar token: {e}")
        
        # Refresh or get new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"[WARNING]  Error refreshing credentials: {e}")
                    self.creds = None
            
            if not self.creds:
                # Need new credentials
                if not config.CALENDAR_CREDENTIALS.exists():
                    print(f"[ERROR] Calendar credentials not found at {config.CALENDAR_CREDENTIALS}")
                    print("[TIP] Download credentials.json from Google Cloud Console")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(config.CALENDAR_CREDENTIALS),
                        config.CALENDAR_SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"[ERROR] Error authenticating: {e}")
                    return False
            
            # Save credentials
            try:
                with open(config.CALENDAR_TOKEN, 'wb') as token:
                    pickle.dump(self.creds, token)
            except Exception as e:
                print(f"[WARNING]  Could not save credentials: {e}")
        
        # Build service
        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
        except Exception as e:
            print(f"[ERROR] Error building calendar service: {e}")
            return False
    
    def create_event(self, event_details: Dict) -> str:
        """
        Create a calendar event
        
        Args:
            event_details: Dict with summary, start, end, etc.
            
        Returns:
            Status message
        """
        if not self.service:
            if not self.authenticate():
                return "[ERROR] Calendar not authenticated"
        
        try:
            event = {
                'summary': event_details.get('summary', 'New Event'),
                'location': event_details.get('location', ''),
                'description': event_details.get('description', ''),
                'start': {
                    'dateTime': event_details['start'],
                    'timeZone': event_details.get('timezone', 'America/Los_Angeles'),
                },
                'end': {
                    'dateTime': event_details['end'],
                    'timeZone': event_details.get('timezone', 'America/Los_Angeles'),
                },
            }
            
            # Add attendees if provided
            if 'attendees' in event_details:
                event['attendees'] = [
                    {'email': email} for email in event_details['attendees']
                ]
            
            # Create event
            result = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return f"[OK] Event created: {result.get('htmlLink', 'Success')}"
            
        except Exception as e:
            return f"[ERROR] Error creating event: {str(e)}"
    
    def list_upcoming_events(self, max_results: int = 10) -> str:
        """
        List upcoming calendar events
        
        Returns:
            Formatted string of events
        """
        if not self.service:
            if not self.authenticate():
                return "[ERROR] Calendar not authenticated"
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return "[CALENDAR] No upcoming events found"
            
            event_lines = ["[CALENDAR] Upcoming events:"]
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', 'No title')
                event_lines.append(f"  - {start}: {summary}")
            
            return "\n".join(event_lines)
            
        except Exception as e:
            return f"[ERROR] Error listing events: {str(e)}"

def parse_event_from_text(text: str) -> Optional[Dict]:
    """
    Parse event details from natural language (simplified)
    
    This is a basic implementation. For production, use NLP or more sophisticated parsing.
    """
    # Example: "Schedule meeting tomorrow at 2pm for 1 hour"
    
    # For now, return a template event
    tomorrow = datetime.now() + timedelta(days=1)
    start = tomorrow.replace(hour=14, minute=0, second=0)
    end = start + timedelta(hours=1)
    
    return {
        'summary': 'Event from voice assistant',
        'description': text,
        'start': start.isoformat(),
        'end': end.isoformat(),
        'timezone': 'America/Los_Angeles'
    }
