"""The definition of Google Calendar App"""

import datetime
import json

import loguru
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from npi.error.auth import UnauthorizedError
from npi.config import config
from npi.app.google import GoogleApp
from npi.app.google.calendar.schema import *
from npi.core import npi_tool, callback
from npiai_proto import api_pb2


# https://developers.google.com/calendar/quickstart/python
# API Reference: https://developers.google.com/calendar/api/v3/reference


class GoogleCalendar(GoogleApp):
    """the function wrapper of Google Calendar App"""

    SCOPE = ["https://www.googleapis.com/auth/calendar"]

    __service_name = "calendar"
    __api_version = "v3"

    def __init__(self, llm=None):
        creds = config.get_google_calendar_credentials()
        if creds is None:
            raise UnauthorizedError(
                "Google Calendar credentials not found, please use `npi auth google calendar` first"
            )
        super().__init__(
            name='google_calendar',
            description='a function that can invoke natural language(English only) instruction to interact with '
                        'Google Calendar, such as create the event, retrieve the events',
            system_role='You are an assistant who are interacting with Google Calendar API. your job is the selecting '
                        'the best function based the tool list.',
            creds=creds.token,
            llm=llm,
            scopes=self.SCOPE,
        )

        self.creds = super()._get_creds()
        self.service = build(
            self.__service_name, self.__api_version, credentials=self.creds
        )

    @npi_tool
    def get_today(self):
        """Get today's date"""
        return datetime.date.today().strftime('%a, %Y-%m-%d')

    @npi_tool
    def get_timezone(self):
        """Get the user's timezone"""
        res = self.service.calendars().get(  # pylint: disable=maybe-no-member
            calendarId='primary'
        ).execute()

        return res.get('timeZone')

    @npi_tool
    async def get_user_email(self, params: GetUserEmailParameters):
        """Get the user's email address"""

        cb = callback.Callable(
            action=api_pb2.ActionRequiredResponse(
                type=api_pb2.ActionType.INFORMATION,  # TODO(wenfeng) Add type of Form
                message=params.message,
            ),
        )
        cb.action.action_id = cb.id()
        await params.get_thread().send_msg(cb=cb)
        loguru.logger.info(f"Waiting for user input")
        result = await cb.wait()
        return result.result.action_result

    @npi_tool
    def retrieve_events(self, params: RetrieveEventsParameters) -> str:
        """Retrieve events from Google Calendar"""
        calendar_id = params.calendar_id
        time_min = params.time_min
        time_max = params.time_max
        max_result = 10
        single_events = True
        order_by = 'startTime'
        event_types = "default"

        try:
            if time_min is None:
                # 'Z' indicates UTC time
                time_min = datetime.datetime.now(
                    datetime.UTC
                ).strftime("%Y-%m-%dT%H:%M:%SZ")  # pylint: disable=maybe-no-member

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

            return json.dumps(events)
        except HttpError as error:
            raise error

    @npi_tool
    def create_event(self, params: CreateEventParameters) -> str:
        """Create and add an event to Google Calendar"""
        summary = params.summary
        description = params.description
        start_time = params.start_time
        end_time = params.end_time
        calendar_id = 'primary'
        attendee = [],
        location = None,
        recurrence = None,
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
                # 'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end_time,  # '2024-04-03T17:00:00-07:00',
                # 'timeZone': 'America/Los_Angeles',
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
