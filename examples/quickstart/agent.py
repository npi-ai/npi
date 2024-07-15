import asyncio

from npiai import agent, Context
from my_tool import MyTool


async def main():
    async with agent.wrap(MyTool()) as tool:
        # make sure you have set the OPENAI_API_KEY in your environment variables
        result = await tool.chat(ctx=Context(), instruction="What's the 10-th fibonacci number?")
        print(f"The answer: {result}")


if __name__ == "__main__":
    asyncio.run(main())
