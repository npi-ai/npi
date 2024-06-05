import asyncio
import os

from openai import OpenAI

from npiai.core import App, npi_tool
from npiai.app.google.gmail import Gmail
from examples.utils import load_gmail_credentials


class MyApp(App):
    def __init__(self):
        super().__init__(
            name='my_app',
            description='test app',
        )

        self.add(Gmail(credentials=load_gmail_credentials()))

    @npi_tool
    def echo(self, v: str):
        """
        Sync echo function.

        Args:
            v: input string
        """
        return v

    @npi_tool
    async def async_echo(self, v: str = 'Hello Async!'):
        """
        Async echo function.

        Args:
            v: input string
        """
        return v


async def main():
    async with MyApp() as my_app:
        # debug fn
        print(
            'Debug:echo:',
            await my_app.debug(
                fn_name='echo',
                args={'v': 'Hello World!'}
            )
        )

        print(
            'Debug:async_echo:',
            await my_app.debug(
                fn_name='async_echo',
            )
        )

        print(
            'Debug:gmail:search_emails:',
            await my_app.debug(
                app_name='gmail',
                fn_name='search_emails',
                args={'max_results': 1}
            )
        )

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
            tools=my_app.tools,  # use npi as a tool package
            tool_choice="auto",
            max_tokens=4096,
        )
        response_message = response.choices[0].message

        messages.append(response_message)

        print(await my_app.call(response_message.tool_calls))


if __name__ == "__main__":
    asyncio.run(main())
