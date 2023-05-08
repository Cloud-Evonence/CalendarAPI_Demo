from flask import Flask, render_template, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
import os


app = Flask(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_credentials():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Flask route to handle the form submission
@app.route('/beautifulschedule', methods=['POST'])
def create_event():
    # Authenticate with Google Calendar API
    creds = get_credentials()

    # Build the Google Calendar API service
    service = build('calendar', 'v3', credentials=creds)

    # Get the form data from the request
    date = request.form['date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    description = request.form['description']
    attendees = request.form['attendees']

    # Construct the start and end time strings for the event
    start_datetime_str = f'{date}T{start_time}:00'
    end_datetime_str = f'{date}T{end_time}:00'

    # Convert the start and end times to UTC time zone
    start_datetime_utc = datetime.fromisoformat(start_datetime_str).astimezone(pytz.utc)
    end_datetime_utc = datetime.fromisoformat(end_datetime_str).astimezone(pytz.utc)

    # Convert the UTC time zone to Indian Standard Time (IST)
    ist = pytz.timezone('Asia/Kolkata')
    start_datetime_ist = start_datetime_utc.astimezone(ist)
    end_datetime_ist = end_datetime_utc.astimezone(ist)

      # Create the event dictionary
    event = {
        'summary': description,
        'start': {
            'dateTime': start_datetime_utc.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_datetime_utc.isoformat(),
            'timeZone': 'UTC',
        },
        'attendees': [{'email': email.strip()} for email in attendees.split('\n')],
        'reminders': {
            'useDefault': True,
        },
    }

    # Insert the event into the user's primary calendar
    try:
        service.events().insert(calendarId='primary', body=event).execute()
        message = 'Event created successfully.'
    except HttpError as error:
        message = f'An error occurred: {error}'

    # Render the response template with the appropriate message
    return render_template('beautifulschedule.html', message=message)

# Flask route to display the form
@app.route('/')
def show_form():
    return render_template('beautifulschedule.html')

if __name__ == '__main__':
    app.run(debug=True)
