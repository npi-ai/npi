import os
from httplib2 import Credentials
from openai import OpenAI
import json

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from npi.core.api import App

__OPENAI_API_KEY = "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"

# https://developers.google.com/calendar/quickstart/python
class GoogleCalendar(App):
    __scopes = ["https://www.googleapis.com/auth/calendar"]
    __service_name = "calendar"
    __api_version = "v3"

    llm = None

    def __init__(self, llm=None):
        self.creds = self.__get_creds()
        self.service = build(self.__service_name, self.__api_version, credentials=self.__get_creds())
        if not llm:
            self.llm = llm
        else:
            # create openai client
            self.llm = OpenAI(api_key=__OPENAI_API_KEY)            
    
    def chat( message="",context=None) -> str:
        return ""

    @staticmethod
    def __get_creds():
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", GoogleCalendar.__scopes)
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

    def __retrive_events(self, calendarId="primary", 
                       timeMin=None, 
                       maxResults=10, 
                       singleEvents=True, 
                       orderBy="startTime",
                       eventTypes="default"
                       ):
        try:
            if timeMin is None:
                timeMin = print(datetime.datetime.utcnow().isoformat() + "Z")  # 'Z' indicates UTC time
                
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendarId,
                    timeMin=timeMin,
                    maxResults=maxResults,
                    singleEvents=singleEvents,
                    orderBy=orderBy,
                    eventTypes=eventTypes,
                ).execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No upcoming events found.")
                return

            # Prints the start and name of the next 10 events
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(json.dumps(event))

        except HttpError as error:
            print(f"An error occurred: {error}")


    def __create_event(self, summary, description, startTime, endTime, 
                     calendarId="primary",
                     attendee=[],
                     localtion=None,
                     recurrence=None,
                     reminders=None):
         
        event = {
            'summary': summary,
            'location': localtion,
            'description': description,
            'start': {
                'dateTime': startTime,
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': endTime, #'2024-04-03T17:00:00-07:00',
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

        event = self.service.events().insert(calendarId=calendarId, body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))        

if __name__ == "__main__":
    gc= GoogleCalendar()
    # gc.retrive_events(calendarId="ww@lifecycle.sh")

    gc.chat("does wells is available on 3pm tommowor?")
    gc.__create_event(summary="Test Event",
                    description="This is a test event", 
                    startTime="2024-04-04T16:00:00-07:00", 
                    endTime="2024-04-04T17:00:00-07:00",
                    attendee=[ {'email': 'w@npi.ai'}])