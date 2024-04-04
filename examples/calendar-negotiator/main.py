
""" the example of the calendar negotiator"""

import json

from openai import OpenAI

from npi.constants.openai import Role
from npi.app.google.calendar import GoogleCalendar
from npi.app.feedback.console import HumanFeedback

PROMPT = """
Your are a calendar negotiator. You have the ability to schedule meetings with anyone, anywhere, anytime.

You can use the tools to help you to schedule the meeting.

the tools you can use are: Google Calendar, Google Gmail.

## Goolge Calendar

1. Use Google Calendar to check the availability of the user.
2. Use Google Calendar to create an event for the user.
3. Use Google Calendar to retrive the events from the user's calendar.


## Google Gmail

1. Use Google Gmail to send an email to the user to ask if a specific time is ok for attenar.

You need to adhere to the following rules step by step to schedule the meeting:

1. You can only schedule the meeting with the user's available time.
2. You must need to follow user's task
3. You must need to collect the enough information to schedule the meeting, such as user's email address, user's available time, etc.
4. If you think you need to ask the user for more information to fill the properties, you can use the tools to ask the user for more information.
5. If the tools don't have the ability to help you gather the information, you can ask the user for the information directly.
"""


if __name__ == "__main__":
    oai = OpenAI(api_key="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")
    gc = GoogleCalendar()
    hb = HumanFeedback()

    msgs = [
        {
            "role": Role.ROLE_SYSTEM.value,
            "content": PROMPT,
        },
        {
            "role":  Role.ROLE_USER.value,
            "content": "schedule a meeting with daofeng for Q2 OKR discussion",
        }
    ]
    # tools = []
    # for func in functions.copy().values():
    #     tools.append({"type": "function", "function": func})

    tools = []
    tools.append(gc.as_tool())
    tools.append(hb.as_tool())
    # print(json.dumps(tools))
    response = oai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=msgs,
        tools=tools,
        tool_choice="auto",
    )

    functions = {
        "google-calendar": gc.chat,
        "human": hb.chat,
    }
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    while tool_calls is not None:
        msgs.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = functions[function_name]
            function_response = function_to_call(
                json.loads(tool_call.function.arguments))
            msgs.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
        second_response = oai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=msgs,
            tools=[gc.as_tool(), hb.as_tool()],
            tool_choice="auto",
        )  # get a new response from the model where it can see the function response
        response_message = second_response.choices[0].message
        tool_calls = response_message.tool_calls
    print(response_message)
