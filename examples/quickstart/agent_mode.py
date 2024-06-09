import asyncio

from npiai import App, agent_wrapper
from npiai.app import Gmail
from npiai.hitl_handler import ConsoleHandler
from examples.utils import load_gmail_credentials


class MyApp(App):
    def __init__(self):
        super().__init__(
            name='my_app',
            description='test app',
        )

        self.use_hitl(ConsoleHandler())

        self.add_tool(
            agent_wrapper(Gmail(credentials=load_gmail_credentials()))
        )


async def main():
    # alternative:
    # app = MyApp()
    # app.add(
    #     create_agent(Gmail(credentials=load_gmail_credentials()))
    # )
    # async with create_agent(app) as agent:
    async with agent_wrapper(MyApp()) as agent:
        agent.export('.cache/agent.yaml')
        print(await agent.chat('get latest email in the inbox'))


if __name__ == "__main__":
    asyncio.run(main())
