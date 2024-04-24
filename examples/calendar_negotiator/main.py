""" the example of the calendar negotiator"""

from openai import OpenAI

from npi.app.google.gmail import Gmail

from npiai.core import Agent
from npiai.app.google import Gmail, Calendar
from npiai.app.human_feedback import ConsoleFeedback

PROMPT = """
Your are a calendar negotiator. You have the ability to schedule meetings with anyone, anywhere, anytime.

You can use the tools to help you to schedule the meeting.

The tools you can use are: Google Calendar, Google Gmail, and Human Feedback:

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
- human_feedback("are you sure to schedule a meeting with test@gmail.com on Friday at <time>?")
- google_calendar("create an event on Friday")
"""


def main():
    negotiator = Agent(
        agent_name='calendar_negotiator',
        description='Schedule meetings with others using gmail and google calendar',
        prompt=PROMPT,
        llm=OpenAI(),
    )

    negotiator.use(Calendar(), Gmail(), ConsoleFeedback())
    print('Negotiator: What\'s your task for me?')
    task = input('User: ')
    print('')
    negotiator.run(task)


if __name__ == "__main__":
    main()
