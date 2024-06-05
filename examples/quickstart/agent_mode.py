import asyncio

from npiai.core import App, create_agent
from npiai.app.google.gmail import Gmail
from examples.utils import load_gmail_credentials


class MyApp(App):
    def __init__(self):
        super().__init__(
            name='my_app',
            description='test app',
        )

        self.add(
            create_agent(Gmail(credentials=load_gmail_credentials()))
        )


async def main():
    async with create_agent(MyApp()) as agent:
        print(await agent.chat('get latest email in the inbox'))


if __name__ == "__main__":
    asyncio.run(main())
