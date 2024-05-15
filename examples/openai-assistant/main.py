import json

from openai import OpenAI
from npiai.app import Gmail, GitHub
from npiai.tools.hitl.console import ConsoleHandler
from npiai.core.toolset import ToolSet
from npiai.integration.oai import EventHandler

client = OpenAI(api_key="xxxxxx")

if __name__ == "__main__":
    gh = GitHub()
    gh.authorize(access_token="")
    ts = (ToolSet.builder().
          use(gh).
          llm(client).
          hitl(ConsoleHandler())
          .build())
    assistant = client.beta.assistants.create(
        name="GitHub Issue Assistant",
        instructions="You are an Assistant can maintain issue comment for repo npi-ai/npi.",
        model="gpt-4o",
        tools=ts.openai(),
    )

    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="what's the latest issue?",
    )

    with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            event_handler=EventHandler(toolset=ts)
    ) as stream:
        stream.until_done()
