"""The definition of Google Calendar App"""

import datetime
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from npiai import function, App


# https://developers.google.com/calendar/quickstart/python
# API Reference: https://developers.google.com/calendar/api/v3/reference


class GoogleCalendar(App):
    def __init__(self, credentials: Credentials):
        super().__init__(
            name='google_calendar',
            description='Manage events on Google Calendar',
            system_prompt='You are an assistant interacting with Google Calendar API. Your job is the selecting the best function based the tool list.',
        )

        self.service = build(
            'calendar', 'v3', credentials=credentials
        )

    @function
    async def get_user_email(self, message: str) -> str:
        """
        Get the user's email address

        Args:
            message: The message to ask the user for their email address
        """
        return await self.hitl.input(self.name, message)

    @function
    def get_today(self):
        """Get today's date"""
        return datetime.date.today().strftime('%a, %Y-%m-%d')

    @function
    def get_timezone(self):
        """Get the user's timezone"""
        res = self.service.calendars().get(  # pylint: disable=maybe-no-member
            calendarId='primary'
        ).execute()

        return res.get('timeZone')

    @function
    def retrieve_events(self, calendar_id: str = 'primary', time_min: str = None, time_max: str = None) -> str:
        """
        Retrieve events from Google Calendar.

        Args:
            calendar_id: The calendar ID which typically in the form of an email address. The primary calendar will be used if not given.
            time_min: Lower bound (exclusive) for an event's end time to filter by. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-05:00. If `time_min` is set, `time_max` must be greater than `time_min`.
            time_max: Upper bound (exclusive) for an event's start time to filter by. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-05T10:00:00-05:00. If `time_max` is set, `time_min` must be smaller than `time_min`.
        """
        calendar_id = calendar_id
        time_min = time_min
        time_max = time_max
        max_result = 10
        single_events = True
        order_by = 'startTime'
        event_types = "default"

        if time_min is None:
            # 'Z' indicates UTC time
            time_min = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")  # pylint: disable=maybe-no-member

        events_result = (
            self.service.events().list(  # pylint: disable=maybe-no-member
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_result,
                singleEvents=single_events,
                orderBy=order_by,
                eventTypes=event_types,
            ).execute()
        )
        events = events_result.get("items", [])

        if not events:
            return "No events found."

        return json.dumps(events, ensure_ascii=False)

    @function
    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        calendar_id: str = 'primary',
        description: str = '',
    ) -> str:
        """
        Create and add an event to Google Calendar.

        Args:
            summary: The summary of the event.
            start_time: The start time of this event. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T09:00:00-05:00. You should retrieve the user's timezone first.
            end_time: The end time of this event. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-05:00. You should retrieve the user's timezone first.
            calendar_id: The calendar ID which typically in the form of an email address. The primary calendar will be used if not given.
            description: The detailed description of the event.
        """
        attendee = [],
        location = None,
        recurrence = None,
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
            },
            'end': {
                'dateTime': end_time,
            },
            'recurrence': [recurrence],
            'attendees': attendee,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        event = self.service.events().insert(  # pylint: disable=maybe-no-member
            calendarId=calendar_id, body=event
        ).execute()

        return f'Event created: {event.get("htmlLink")}'
