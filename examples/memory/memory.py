from typing import Annotated
from npiai import FunctionTool, function, FromContext, agent, Context
from npiai.hitl_handler import ConsoleHandler
import asyncio


class MyTool(FunctionTool):
    name = "my_tool"
    description = "My first NPi tool"

    @function
    def get_test_id(
        self,
        test_id: Annotated[int, FromContext(query="{user} test id")],
    ):
        """
        Get test id

        Args:
            test_id: test id
        """
        return test_id


async def main():
    async with agent.wrap(MyTool()) as tool:
        tool.use_hitl(ConsoleHandler())
        ctx = Context()
        ctx.bind(tool)
        result = await tool.chat(ctx=ctx, instruction="What's the test id for @Alice?")
        print(f"Result: {result}")

        result = await tool.chat(ctx=ctx, instruction="What's the test id for @Bob?")
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
