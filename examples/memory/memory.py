from typing import Annotated
from npiai import FunctionTool, function, FromVectorDB, agent, Context
from npiai.hitl_handler import ConsoleHandler
import asyncio


class MyTool(FunctionTool):
    name = "my_tool"
    description = "My first NPi tool"

    @function
    def get_test_id(
        self,
        test_id: Annotated[int, FromVectorDB(query="{user}'s test id")],
    ):
        """
        Get test id

        Args:
            test_id: test id
        """
        return test_id


async def main():
    async with agent.wrap(MyTool()) as tool:
        ctx = Context()
        ctx.use_hitl(ConsoleHandler())
        result = await tool.chat(ctx=ctx, instruction="What's the test id for @Alice?")
        print(f"Result: {result}")

        result = await tool.chat(ctx=ctx, instruction="What's the test id for @Bob?")
        print(f"Result: {result}")

        result = await tool.chat(
            ctx=ctx, instruction="What are the test id's for @Alice and @Bob?"
        )
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
