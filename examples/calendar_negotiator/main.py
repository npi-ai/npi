""" the example of the calendar negotiator"""
import asyncio
import os

from npiai import App, agent_wrapper
from npiai.app import Gmail, GoogleCalendar
from npiai.hitl_handler import ConsoleHandler
from npiai import OpenAI

from examples.utils import load_gmail_credentials, load_google_calendar_credentials

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


class Negotiator(App):
    def __init__(self):
        super().__init__(
            name='calendar_negotiator',
            description='Schedule meetings with others using gmail and google calendar',
            system_prompt=PROMPT,
        )

        self.use_hitl(ConsoleHandler())

        self.add(
            agent_wrapper(GoogleCalendar(credentials=load_google_calendar_credentials())),
            agent_wrapper(Gmail(credentials=load_gmail_credentials())),
        )


async def run():
    llm = OpenAI(model='gpt-4-turbo-preview', api_key=os.environ['OPENAI_API_KEY'])

    async with agent_wrapper(Negotiator(), llm=llm) as negotiator:
        print("Negotiator: What's your task for me?")
        task = input('User: ')
        print('')
        await negotiator.chat(task)


def main():
    # poetry entry
    asyncio.run(run())


if __name__ == "__main__":
    main()
