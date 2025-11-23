#!/usr/bin/env python3
"""
Google Calendar Event Fetcher
Fetches events from all user calendars for a configurable number of days
and formats them according to the specified JSON structure.
"""

import json
import os
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_credentials_from_env() -> Optional[Dict]:
    """Build credentials dict from environment variables."""
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    project_id = os.getenv('GOOGLE_PROJECT_ID')
    
    if not all([client_id, client_secret, project_id]):
        return None
    
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "project_id": project_id,
            "auth_uri": os.getenv('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            "token_uri": os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            "auth_provider_x509_cert_url": os.getenv(
                'GOOGLE_AUTH_PROVIDER_X509_CERT_URL',
                'https://www.googleapis.com/oauth2/v1/certs'
            ),
            "redirect_uris": os.getenv('GOOGLE_REDIRECT_URIS', 'http://localhost').split(',')
        }
    }


def get_calendar_service():
    """Authenticate and return a Google Calendar API service object."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_dict = get_credentials_from_env()
            
            if credentials_dict:
                flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)
                creds = flow.run_local_server(port=0)
            elif os.path.exists('credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise FileNotFoundError(
                    "No credentials found. Please either:\n"
                    "1. Set up .env file with GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_PROJECT_ID\n"
                    "2. Or download credentials.json from Google Cloud Console\n"
                    "See README.md for instructions."
                )
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)


def parse_datetime(dt_str: str, timezone_str: Optional[str] = None) -> datetime:
    """Parse ISO datetime string to datetime object and convert to local timezone."""
    if 'T' in dt_str:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    else:
        dt = datetime.fromisoformat(dt_str)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    else:
        dt = dt.astimezone()
    
    return dt


def format_time(dt: datetime) -> str:
    """Format datetime to HH:MM string."""
    return dt.strftime('%H:%M')


def calculate_duration_minutes(start_dt: datetime, end_dt: datetime) -> int:
    """Calculate duration in minutes between two datetimes."""
    delta = end_dt - start_dt
    return int(delta.total_seconds() / 60)


def get_all_calendars(service) -> List[Dict]:
    """Get a list of all calendars the user has access to."""
    try:
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        return calendars
    except HttpError as error:
        print(f'An error occurred while fetching calendar list: {error}')
        raise


def fetch_calendar_events(service, calendar_id: str, calendar_name: str, time_min: datetime, time_max: datetime) -> List[Dict]:
    """Fetch events from a specific calendar within the given time range."""
    try:
        if time_min.tzinfo is None:
            time_min = time_min.replace(tzinfo=datetime.now().astimezone().tzinfo)
        if time_max.tzinfo is None:
            time_max = time_max.replace(tzinfo=datetime.now().astimezone().tzinfo)
        
        # Add 1 day to ensure all-day events on the last day are captured (API uses exclusive end time)
        time_max_inclusive = time_max + timedelta(days=1)
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat(),
            timeMax=time_max_inclusive.isoformat(),
            maxResults=2500,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        for event in events:
            event['_calendar_name'] = calendar_name
            event['_calendar_id'] = calendar_id
        
        return events
    except HttpError as error:
        print(f'  Warning: Could not fetch events from "{calendar_name}": {error}')
        return []


def process_event(event: Dict) -> List[Dict]:
    """Process a single event and extract required fields.
    Returns a list of event dicts (one per day for multi-day events)."""
    start = event.get('start', {})
    end = event.get('end', {})
    
    is_all_day = 'date' in start and 'date' in end
    
    if is_all_day:
        start_date_str = start.get('date')
        end_date_str = end.get('date')
        
        start_dt = datetime.fromisoformat(start_date_str)
        end_dt = datetime.fromisoformat(end_date_str)
        
        # Google Calendar API uses exclusive end dates for all-day events
        end_dt = end_dt - timedelta(days=1)
        
        event_data = {
            'start_time': '00:00',
            'end_time': '23:59',
            'duration_minutes': 1440,
            'title': event.get('summary', ''),
            'location': event.get('location') or None,
            'is_all_day': True
        }
        
        events_list = []
        current_date = start_dt
        while current_date <= end_dt:
            event_entry = event_data.copy()
            event_entry['date'] = current_date.strftime('%Y-%m-%d')
            events_list.append(event_entry)
            current_date += timedelta(days=1)
        
        return events_list
    else:
        # Timed event
        start_dt_str = start.get('dateTime')
        end_dt_str = end.get('dateTime')
        
        if not start_dt_str or not end_dt_str:
            return []
        
        start_dt = parse_datetime(start_dt_str)
        end_dt = parse_datetime(end_dt_str)
        
        events_list = []
        current_date = start_dt.date()
        end_date = end_dt.date()
        
        while current_date <= end_date:
            if current_date == start_dt.date() and current_date == end_dt.date():
                event_entry = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'start_time': format_time(start_dt),
                    'end_time': format_time(end_dt),
                    'duration_minutes': calculate_duration_minutes(start_dt, end_dt),
                    'title': event.get('summary', ''),
                    'location': event.get('location') or None,
                    'is_all_day': False
                }
            elif current_date == start_dt.date():
                end_of_day = datetime.combine(current_date, time(23, 59, 0))
                if start_dt.tzinfo:
                    end_of_day = end_of_day.replace(tzinfo=start_dt.tzinfo)
                event_entry = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'start_time': format_time(start_dt),
                    'end_time': '23:59',
                    'duration_minutes': calculate_duration_minutes(start_dt, end_of_day),
                    'title': event.get('summary', ''),
                    'location': event.get('location') or None,
                    'is_all_day': False
                }
            elif current_date == end_dt.date():
                start_of_day = datetime.combine(current_date, time(0, 0, 0))
                if end_dt.tzinfo:
                    start_of_day = start_of_day.replace(tzinfo=end_dt.tzinfo)
                event_entry = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'start_time': '00:00',
                    'end_time': format_time(end_dt),
                    'duration_minutes': calculate_duration_minutes(start_of_day, end_dt),
                    'title': event.get('summary', ''),
                    'location': event.get('location') or None,
                    'is_all_day': False
                }
            else:
                event_entry = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'start_time': '00:00',
                    'end_time': '23:59',
                    'duration_minutes': 1440,
                    'title': event.get('summary', ''),
                    'location': event.get('location') or None,
                    'is_all_day': False
                }
            
            events_list.append(event_entry)
            current_date += timedelta(days=1)
        
        return events_list


def organize_events_by_days(events: List[Dict], start_date: datetime, num_days: int) -> Dict:
    """Organize events into the required JSON structure for the specified number of days."""
    week_start = start_date
    week_end = week_start + timedelta(days=num_days - 1)
    
    days = []
    for day_offset in range(num_days):
        current_date = week_start + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        weekday = current_date.strftime('%A')
        
        day_events = []
        for event in events:
            event_date = event.get('date')
            if event_date == date_str:
                day_events.append({
                    'title': event.get('title', ''),
                    'start_time': event.get('start_time', ''),
                    'end_time': event.get('end_time', ''),
                    'duration_minutes': event.get('duration_minutes', 0),
                    'location': event.get('location'),
                    'is_all_day': event.get('is_all_day', False)
                })
        
        days.append({
            'date': date_str,
            'weekday': weekday,
            'events': day_events
        })
    
    return {
        'week_start': week_start.strftime('%Y-%m-%d'),
        'week_end': week_end.strftime('%Y-%m-%d'),
        'days': days
    }


def main():
    """Main function to fetch and process calendar events."""
    # Get number of days from environment variable
    days_to_fetch = os.getenv('DAYS_TO_FETCH')
    if not days_to_fetch:
        raise ValueError(
            "DAYS_TO_FETCH environment variable is required. "
            "Please set it in your .env file (e.g., DAYS_TO_FETCH=7)"
        )
    num_days = int(days_to_fetch)
    
    print("Authenticating with Google Calendar API...")
    service = get_calendar_service()
    
    print("Fetching list of calendars...")
    calendars = get_all_calendars(service)
    print(f"Found {len(calendars)} calendar(s)")
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today + timedelta(days=num_days - 1)
    
    print(f"\nFetching events from {today.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({num_days} days)...")
    print("Fetching events from all calendars...")
    
    all_raw_events = []
    for calendar in calendars:
        calendar_id = calendar.get('id')
        calendar_name = calendar.get('summary', 'Unnamed Calendar')
        print(f"  - {calendar_name} ({calendar_id})")
        
        events = fetch_calendar_events(service, calendar_id, calendar_name, today, end_date)
        all_raw_events.extend(events)
        print(f"    Found {len(events)} event(s)")
    
    print(f"\nTotal events found: {len(all_raw_events)}")
    
    processed_events = []
    for event in all_raw_events:
        processed_list = process_event(event)
        if processed_list:
            processed_events.extend(processed_list)
    
    result = organize_events_by_days(processed_events, today, num_days)
    
    output_file = 'calendar_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ JSON file saved to: {output_file}")
    print("\n" + "="*80)
    print("FINAL JSON OUTPUT:")
    print("="*80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*80)


if __name__ == '__main__':
    main()
