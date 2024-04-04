
""" the example of the calendar negotiator"""

from openai import OpenAI

from npi.constants.openai import Role
from npi.app.google.calendar import GoogleCalendar

PROMPT = """
Your are the calendar negotiator. You have the power to schedule meetings with anyone, anywhere, anytime.

The tool you can use are: Goolge Gmail and Goolge Calendar.

1. Use Google Gmail to send an email to the user to ask if a specific time is ok for attenar.
"""


if __file__ == "__main__":
    oai = OpenAI(api_key="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")
    gc = GoogleCalendar()

    response = oai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": Role.ROLE_SYSTEM.value,
                "content": PROMPT,
            },
            {
                "role":  Role.ROLE_USER.value,
                "content": "schedule a meeting with daofeng for Q2 OKR discussion",
            }
        ],
        tools=[gc.as_tool()],
        tool_choice="auto",
    )
