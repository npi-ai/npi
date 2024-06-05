import asyncio
import os

from openai import OpenAI

from npiai.app.google.gmail import Gmail
from examples.utils import load_gmail_credentials


async def main():
    async with Gmail(credentials=load_gmail_credentials()) as gmail:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        messages = [
            {
                "role": "user",
                "content": "get latest email in the inbox",
            }
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=gmail.tools,  # use npi as a tool package
            tool_choice="auto",
            max_tokens=4096,
        )
        response_message = response.choices[0].message

        messages.append(response_message)

        print(await gmail.call(response_message.tool_calls))


if __name__ == "__main__":
    asyncio.run(main())
