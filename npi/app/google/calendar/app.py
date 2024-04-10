"""The definition of Google Calendar App"""

import os.path
import json
import datetime
from typing import List

from openai import OpenAI
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from npi.core import App, npi_tool
from npi.types import FunctionRegistration

from npi.app.google.calendar.schema import *


# https://developers.google.com/calendar/quickstart/python
# API Reference: https://developers.google.com/calendar/api/v3/reference


class GoogleCalendar(App):
    """the function wrapper of Google Calendar App"""

    __scopes = ["https://www.googleapis.com/auth/calendar"]
    __service_name = "calendar"
    __api_version = "v3"

    llm = None

    def __init__(self, llm=None):
        super().__init__(
            name='google_calendar',
            description='a function that can invoke natural language(English only) instruction to interact with Google Calendar, such as create the event, retrieve the events',
            system_role='You are an assistant who are interacting with Google Calendar API. your job is the selecting the best function based the tool list.',
            llm=llm,
        )

        self.creds = self.__get_creds()
        self.service = build(
            self.__service_name, self.__api_version, credentials=self.__get_creds()
        )
        if llm:
            self.llm = llm
        else:
            # create openai client
            self.llm = OpenAI(
                api_key="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"
            )

    def get_functions(self) -> List[FunctionRegistration]:
        return [
            FunctionRegistration(
                fn=self.__create_event,
                Params=CreateEventParameters,
                description='Create and add an event to Google Calendar',
            ),
            FunctionRegistration(
                fn=self.__retrieve_events,
                Params=RetrieveEventsParameters,
                description='Retrieve events from Google Calendar',
            ),
            FunctionRegistration(
                fn=self.__get_today,
                description='Get today\'s date',
            ),
            FunctionRegistration(
                fn=self.__get_timezone,
                description='Get the user\'s timezone'
            )
        ]

    @staticmethod
    def __get_creds():
        creds = None
        if os.path.exists("credentials/gc_token.json"):
            with open("credentials/gc_token.json", encoding="utf-8") as file:
                creds = Credentials.from_authorized_user_info(
                    json.load(file), GoogleCalendar.__scopes
                )

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials/google.json", GoogleCalendar.__scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("credentials/gc_token.json", "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        return creds

    @npi_tool
    def __get_today(self):
        """Get today's date"""
        return datetime.date.today().strftime('%a, %Y-%m-%d')

    @npi_tool
    def __get_timezone(self):
        """Get the user's timezone"""
        res = self.service.calendars().get(  # pylint: disable=maybe-no-member
            calendarId='primary'
        ).execute()

        return res.get('timeZone')

    @npi_tool
    def __retrieve_events(self, params: RetrieveEventsParameters) -> str:
        """Retrieve events from Google Calendar"""
        calendar_id = 'primary'
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
    def __create_event(self, params: CreateEventParameters) -> str:
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
