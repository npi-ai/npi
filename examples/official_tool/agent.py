import asyncio
import json
import os

from openai import OpenAI

from npiai import agent, FunctionTool
from npiai.tools import GitHub


class MyTool(FunctionTool):
    name = "my_tool"
    description = "my first tool for OpenAI Function calling"

    def __init__(self):
        super().__init__()
        self.add_tool(
            # Get your Access token at https://github.com/settings/tokens
            agent.wrap(GitHub(access_token=os.environ.get("GITHUB_ACCESS_TOKEN", None)))
        )


async def main():
    tool = MyTool()
    await tool.start()

    print(json.dumps(tool.tools, indent=2))  # view function definition
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    messages = [
        {
            "role": "user",
            "content": "what's the title of the PR #1 of npi-ai/npi",
        }
    ]
    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tool.tools,  # use agent as a functions tool
            tool_choice="auto",
            max_tokens=4096,
        )

        response_message = response.choices[0].message

        if response_message.tool_calls:
            messages.append(response_message)
            messages.extend(await tool.call(tool_calls=response_message.tool_calls))
        else:
            print(response_message.content)
            break

    await tool.end()


if __name__ == "__main__":
    asyncio.run(main())
