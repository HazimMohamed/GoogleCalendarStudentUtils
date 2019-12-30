import datetime

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from common import DayOfTheWeek
import os
import pickle


class GoogleCalendarAPIWrapper:

    def __init__(self, timezone_str: str = 'US/Eastern'):
        scopes = ['https://www.googleapis.com/auth/calendar']
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file='google_calendar_api/credentials.json',
                                                         scopes=scopes)
        pickle_file = 'google_calendar_api/stored_creds/creds.pickle'
        if os.path.exists(pickle_file):
            with open(pickle_file, 'rb') as pickle_obj:
                creds = pickle.load(pickle_obj)
        else:
            creds = flow.run_local_server()
            with open(pickle_file, 'wb') as pickle_obj:
                pickle.dump(creds, pickle_obj)
        self.service = build('calendar', 'v3', credentials=creds)
        self.timezone = timezone_str

    def add_weekly_event(self, name: str, repeats_on: DayOfTheWeek,
                         start_time: datetime.time, end_time: datetime.time,
                         start_date: datetime.date, end_date: datetime.date,
                         location: str = None, comments: str = None):
        start_date = DayOfTheWeek.find_first_day_after_date(start_date, repeats_on)
        first_time_start = datetime.datetime.combine(start_date, start_time)
        first_time_end = datetime.datetime.combine(start_date, end_time)
        event = {
            'summary': name,
            'start': {
                'dateTime': first_time_start.isoformat(),
                'timeZone': self.timezone
            },
            'end': {
                'dateTime': first_time_end.isoformat(),
                'timeZone': self.timezone
            },
            'recurrence': [
                f'RRULE:FREQ=WEEKLY;UNTIL={end_date.strftime("%Y%m%dT000000Z")};BYDAY={repeats_on.to_gday()}'
            ]
        }

        if location:
            event['location'] = location

        if comments:
            event['description'] = comments

        new_event = self.service.events().insert(calendarId='primary', body=event).execute()
        print(f'Event created: {new_event.get("htmlLink")}')


if __name__ == '__main__':
    # test call
    GoogleCalendarAPIWrapper().add_weekly_event('Test', DayOfTheWeek.THURSDAY,
                                                datetime.time(hour=9), datetime.time(hour=17),
                                                datetime.date.today(),
                                                datetime.date.today() + datetime.timedelta(weeks=4))
