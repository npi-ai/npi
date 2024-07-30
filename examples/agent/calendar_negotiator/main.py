""" the example of the calendar negotiator"""

import asyncio
import os
from typing import List
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from npiai import FunctionTool, agent, OpenAI
from npiai.context import Context
from npiai.tools import Gmail, GoogleCalendar
from npiai.hitl_handler import ConsoleHandler


PROMPT = """
Your are a calendar negotiator. You have the ability to schedule meetings with anyone, anywhere, anytime.

You can use the tools to help you to schedule the meeting.

The tools you can use are: Google Calendar and Gmail:

## Instructions

You need to follow the instructions below step by step to schedule the meeting:

1. Ask for the attendee's email address if not provided.
2. Look for the user's available time slots from on Google Calendar if not provided.
3. If the previous step fails, ask the user for available time slots.
4. After the available time slots are determined, you should send an email to the attendee. 
5. Wait for the attendee's reply to the email you sent. Do not proceed if the reply is not received.
6. If the proposed dates are not available for the attendee, try again to schedule a new date.
7. If the conversation reaches an agreement, you should create an event on the user's calendar.
8. If email not provided, you can use 'console_feedback' to ask for providing email.

## Rules

Here are some rules for you to fulfill the task:

1. You can only schedule the meeting with the user's available time.
2. You must follow user's task.
3. The Google Calendar tool can only be used to manage the user's schedule, not the attendee's schedule.
3. If you think you need to ask the user for more information to fill the properties, you can use the Human Feedback tool to ask the user for more information.
4. If you need confirmation from the user to complete the task, or you want to ask the user a question, you can use the Human Feedback tool to do so. Especially, if the last assistant's message proposed a question, you should ask the user for response.

## Example
Task: Schedule a meeting with test@gmail.com on Friday
Steps:
- google_calendar("check the {user_email_address} availability on Friday")
- gmail("send an email to test@gmail.com asking their availability on Friday")
- gmail("wait for response from test@gmail.com")
- confirm_action("are you sure to schedule a meeting with test@gmail.com on Friday at <time>?")
- google_calendar("create an event on Friday")
"""


def load_google_credentials(secret_file: str, scopes: List[str], token_file: str):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file=secret_file, scopes=scopes
            )
            creds = flow.run_local_server(port=19876, redirect_uri_trailing_slash=False)
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return creds


class Negotiator(FunctionTool):
    name = "calendar_negotiator"
    description = "Schedule meetings with others using gmail and google calendar"
    system_prompt = PROMPT

    def __init__(self, secret_file: str, token_file: str = ""):
        super().__init__()
        if token_file == "":
            token_file = secret_file.replace("secret", "token")

        cred = load_google_credentials(
            token_file=token_file,
            secret_file=secret_file,
            scopes=[
                "https://mail.google.com/",
                "https://www.googleapis.com/auth/calendar",
            ],
        )

        self.add_tool(
            agent.wrap(GoogleCalendar(creds=cred)),
            agent.wrap(Gmail(creds=cred)),
        )

        self.use_hitl(ConsoleHandler())


async def run():
    llm = OpenAI(model="gpt-4-turbo-preview", api_key=os.environ["OPENAI_API_KEY"])

    # You could get Google Secret JSON file on https://console.cloud.google.com/apis/credentials by steps:
    #
    # 1. Open: https://console.cloud.google.com/apis/credentials
    # 2. Click 'CREATE CREDENTIALS'
    # 3. Select 'OAuth client ID'
    # 4. Click 'Application type' and select 'Web application'
    # 5. Click 'Add URI' then type into 'http://localhost:19876' at Authorized redirect URIs
    # 6. Click 'Create'
    # 7. Download JSON
    #
    # You may need to enable Google Calendar API and Gmail API in your Google Cloud Console.

    nego = Negotiator(secret_file=f"{Path.cwd()}/secret.example.json")
    async with agent.wrap(nego, llm=llm) as negotiator:
        print("Negotiator: What's your task for me?")
        task = input("User: ")
        print("")

        print(await negotiator.chat(ctx=Context(), instruction=task))


def main():
    # poetry entry
    asyncio.run(run())


if __name__ == "__main__":
    main()
