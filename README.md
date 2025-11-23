# Google Calendar Event Fetcher

A Python script that fetches events from all your Google Calendars and exports them to a structured JSON file. Perfect for integrating calendar data into your applications, dashboards, or automation workflows.

## Features

- ✅ Fetches events from **all** your Google Calendars
- ✅ Configurable date range (set via environment variable)
- ✅ Handles both timed events and all-day events
- ✅ Splits multi-day events across multiple days
- ✅ Clean, structured JSON output
- ✅ Simple setup with environment variables
- ✅ OAuth 2.0 authentication (one-time setup)

## Use Cases

- Build custom calendar dashboards
- Integrate calendar data into other applications
- Automate calendar-based workflows
- Export calendar data for analysis
- Sync calendar events to other systems


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
