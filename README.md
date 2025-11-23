# Google Calendar Event Fetcher

This script fetches events from all your Google Calendars for a configurable number of days (including today) and formats them into a structured JSON file.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Calendar API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials JSON file

### 3. Configure Environment Variables

Create a `.env` file in the project directory with the required configuration:

```env
# Number of days to fetch events for (required)
DAYS_TO_FETCH=7

# Google OAuth credentials (extract from the downloaded credentials.json)
# Find these values in the "installed" section of the JSON file:
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_PROJECT_ID=your_project_id
```

**Note:** You can use either the `.env` file with the credentials above, or place the downloaded `credentials.json` file in this directory. The script will prefer environment variables if both are available.

### 4. Run the Script

```bash
python fetch_calendar.py
```

On first run, the script will:
- Open a browser window for you to authenticate with Google
- Save your credentials to `token.json` for future runs
- Fetch events from all your calendars
- Generate `calendar_events.json` with the formatted data

## Output Format

The script generates a JSON file with the following structure:

```json
{
  "week_start": "YYYY-MM-DD",
  "week_end": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "weekday": "Monday",
      "events": [
        {
          "title": "Event Title",
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "duration_minutes": 60,
          "location": "Location or null",
          "is_all_day": false
        }
      ]
    }
  ]
}
```
