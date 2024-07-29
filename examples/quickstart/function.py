import asyncio
import json
import os

from openai import OpenAI
from my_tool import MyTool


async def main():
    async with MyTool() as tool:
        print(f"The schema of the tool is\n\n {json.dumps(tool.tools, indent=2)}")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        messages = [
            {
                "role": "user",
                "content": "What's the 10-th fibonacci number?",
            }
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tool.tools,  # use GitHub tool as functions package
            tool_choice="auto",
            max_tokens=4096,
        )
        response_message = response.choices[0].message
        if response_message.tool_calls:
            result = await tool.call(tool_calls=response_message.tool_calls)
            print(f"The result of function\n\n {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
