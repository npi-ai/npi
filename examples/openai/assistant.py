
from openai import OpenAI
from npiai.app import Gmail, GitHub
from npiai.tools.hitl.console import ConsoleHandler
from npiai.core.toolset import ToolSet
from npiai.integration.oai import EventHandler


if __name__ == "__main__":
    client = OpenAI(api_key="xxxxx")
    ts = ToolSet(
        llm=client,
        hitl_handler=ConsoleHandler(),
        tools=[
            GitHub(access_token="xxxxx"),
        ],
    )

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
        content="what's title of issue #27 of repo npi-ai/npi?",
    )

    def stream_handler(run_id: str, stream):
        for text in stream.text_deltas:
            print(text, end="", flush=True)

    eh = EventHandler(toolset=ts, llm=client, thread_id=thread.id, stream_handler=stream_handler)
    with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            event_handler=eh,
    ) as _stream:
        _stream.until_done()
