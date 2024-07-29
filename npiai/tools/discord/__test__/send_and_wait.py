import asyncio

from npiai import agent
from npiai.tools import Discord
from npiai.hitl_handler import ConsoleHandler


async def main():
    async with agent.wrap(Discord()) as agent_tool:
        agent_tool.use_hitl(ConsoleHandler())
        return await agent_tool.chat(
            "Send a direct message to Dolphin asking if he is doing well, and wait for his reply."
        )


if __name__ == "__main__":
    asyncio.run(main())
