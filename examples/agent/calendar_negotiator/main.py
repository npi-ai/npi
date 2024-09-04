""" the example of the calendar negotiator"""

import asyncio
import json
import os
from typing import List
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from npiai import FunctionTool, agent, OpenAI, function
from npiai.core.planner import StepwisePlanner
from npiai.core.optimizer import DedupOptimizer
from npiai.context import Context
from npiai.tools import Gmail, GoogleCalendar
from npiai.hitl_handler import ConsoleHandler
from npiai.types import RuntimeMessage
from npiai.utils import logger

RULES = """
- You should Gather all necessary details for the meeting, including the preferred time and date, the duration, and the email addresses of attendees. If this information is not provided upfront, request it using the `ask_human` tool.
- You should check the user's availability via Google Calendar.
- You must send an invitation email to the intended attendee(s) to propose the meeting time, await their response, and adjust the schedule as needed based on their availability.
- No need to create a draft email for the user to review. You can directly send the email to the attendee(s).
- The Google Calendar tool can only be used to manage the user's schedule, not the attendee's schedule.
- If you think you need to ask the user for more information to fill the properties, you can use the `ask_human` tool to ask the user for more information.
- If you need confirmation from the user to complete the task, or you want to ask the user a question, you can use the `ask_human` tool to do so. Especially, if the last assistant's message proposed a question, you should ask the user for response.
"""


PROMPT = f"""
Your are a calendar negotiator with the ability to schedule meetings with anyone, anywhere, anytime.
"""


class DebugContext(Context):
    async def send(self, msg: RuntimeMessage):
        match msg["type"]:
            case "message":
                logger.info(msg["message"])
            case "execution_result":
                logger.info(msg["result"])
            case "debug":
                logger.debug(msg["message"])
            case "error":
                logger.error(msg["message"])
            case _:
                logger.info(f"Context Message: {msg}")


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

    @function
    async def ask_human(self, ctx: Context, question: str):
        """
        Ask human to provide information.

        Args:
            ctx: NPi Context
            question: Question to ask
        """

        return await ctx.hitl.input(
            tool_name=self.name,
            message=question,
        )


async def run():
    llm = OpenAI(model="gpt-4o", api_key=os.environ["OPENAI_API_KEY"])

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

    # nego = Negotiator(secret_file=f"{Path.cwd()}/secret.example.json")
    nego = Negotiator(secret_file="./credentials/google_secret.json")

    async with agent.wrap(nego) as negotiator:
        ctx = DebugContext()
        ctx.use_llm(llm)
        ctx.use_hitl(ConsoleHandler())

        print("Negotiator: What's your task for me?")
        task = input("User: ")
        print("")

        planner = StepwisePlanner(rules=RULES)
        plan = await planner.generate_plan(
            ctx=ctx,
            task=task,
            tool=negotiator,
        )

        print("Plan:", json.dumps(plan.to_json_object(), indent=2))

        optimizer = DedupOptimizer(rules=RULES)
        optimized_plan = await optimizer.optimize(ctx, plan)

        print("Optimized Plan:", json.dumps(optimized_plan.to_json_object(), indent=2))

        print(await negotiator.execute_plan(ctx, optimized_plan))


def main():
    # poetry entry
    asyncio.run(run())


if __name__ == "__main__":
    main()
