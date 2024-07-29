import asyncio
import json
import os

from openai import OpenAI
from npiai.tools import GitHub


async def main():
    # Get your Access token at https://github.com/settings/tokens
    async with GitHub(access_token=os.environ.get("GITHUB_ACCESS_TOKEN", None)) as gh:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        messages = [
            {
                "role": "user",
                "content": "what's the title of the PR #1 of npi-ai/npi",
            }
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=gh.tools,  # use GitHub tool as functions package
            tool_choice="auto",
            max_tokens=4096,
        )
        response_message = response.choices[0].message
        if response_message.tool_calls:
            result = await gh.call(tool_calls=response_message.tool_calls)
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
