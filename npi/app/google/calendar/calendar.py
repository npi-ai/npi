"""the defination of Google Calendar App"""

import os.path
import json
import datetime

from openai import OpenAI
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from npi.core.api import App
from npi.constants.openai import Role

# https://developers.google.com/calendar/quickstart/python
# API Reference: https://developers.google.com/calendar/api/v3/reference


class GoogleCalendar(App):
    """the function wrapper of Google Calendar App"""

    __calendar_funcs = {
        "create_event": {
            "name": "create_event",
            "description": "create the event to Google Calendar",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "the title of this event",
                    },
                    "description": {
                        "type": "string",
                        "description": "the description of this event. this property",
                    },
                    "startTime": {
                        "type": "string",
                        "description": "the start time of this event",
                    },
                    "endTime": {
                        "type": "string",
                        "description": "the end time of this event",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["summary", "description", "startTime", "endTime"],
            },
        },

        "retrive_events": {
            "name": "retrive_events",
            "description": "retrive the events from Google Calendar",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "the calendar identifier, which is the email address of the user. if the context doesn't contain the email address, you should ask the user to provide the email address",
                    },
                },
                "required": ["calendar_id"],
            },
        },
        "get_user_email": {
            "name": "get_user_email",
            "description": "get the current user email address",
        }
    }

    __scopes = ["https://www.googleapis.com/auth/calendar"]
    __service_name = "calendar"
    __api_version = "v3"
    __system_role = '''
    You are an assistant who are interacting with Google Calendar API. your job is the selecting the best function based the tool list.
    '''

    llm = None

    def __init__(self, llm=None):
        super().__init__(llm)

        self.creds = self.__get_creds()
        self.service = build(
            self.__service_name, self.__api_version, credentials=self.__get_creds())
        if llm:
            self.llm = llm
        else:
            # create openai client
            self.llm = OpenAI(
                api_key="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")

        super()._register_functions({
            "create_event": self.__create_event,
            "retrive_events": self.__retrive_events,
            "get_user_email": self.__get_user_email,
        })

    def chat(self, message, context=None) -> str:
        messages = [
            {"role": Role.ROLE_SYSTEM.value, "content": self.__system_role, },
            {"role": Role.ROLE_USER.value, "content": message, },
        ]

        super()._call_llm(messages, self.__calendar_funcs)

        # self.__create_event(summary="Test Event",
        #                     description="This is a test event",
        #                     start_time="2024-04-04T16:00:00-07:00",
        #                     end_time="2024-04-04T17:00:00-07:00",
        #                     attendee=[{'email': 'w@npi.ai'}])
        return ""

    @staticmethod
    def __get_creds():
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_info(
                json.load(open("token.json")), GoogleCalendar.__scopes
            )
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", GoogleCalendar.__scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        return creds

    def __get_user_email(self, params):
        return "ww@lifecycle.sh"

    def __retrive_events(self, params,):
        calendar_id = params['calendar_id']
        time_min = None,
        max_result = 10,
        single_events = True,
        order_by = "startTime",
        event_types = "default"

        try:
            if time_min is None:
                # 'Z' indicates UTC time
                time_min = print(datetime.datetime.utcnow().isoformat() + "Z")

            events_result = (
                self.service.events()
                .list(
                    calendar_id=calendar_id,
                    time_min=time_min,
                    max_result=max_result,
                    single_events=single_events,
                    order_by=order_by,
                    event_types=event_types,
                ).execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No upcoming events found.")
                return

            # Prints the start and name of the next 10 events
            for event in events:
                start = event["start"].get(
                    "dateTime", event["start"].get("date"))
                print(json.dumps(event))

        except HttpError as error:
            print(f"An error occurred: {error}")

    def __create_event(self, params):
        summary = params['summary']
        description = params['description']
        start_time = params['start_time']
        end_time = params['end_time']
        calendar_id = params['end_time']
        attendee = [],
        localtion = None,
        recurrence = None,
        event = {
            'summary': summary,
            'location': localtion,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end_time,  # '2024-04-03T17:00:00-07:00',
                'timeZone': 'America/Los_Angeles',
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

        event = self.service.events().insert(
            calendar_id=calendar_id, body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))


if __name__ == "__main__":
    gc = GoogleCalendar()
    gc.chat("does wells is available on 3pm tommowor?")
