from typing import Annotated
from npiai import FunctionTool, function, FromContext, agent, Context, LLM, Source, Description, Field, Schema
from npiai.hitl_handler import ConsoleHandler
import asyncio


class MyTool(FunctionTool):
    name = "my_tool"
    description = "My first NPi tool"

    @function
    def get_test_id(
        self,
        ctx,
        target_user: str,
    ):
        """
        Get test id
        """

        ctx.rag(query="xxxxxx") # => c
        ctx.kv.get("channel_id") # => d
        obj = Schema()
        ctx.sql.exec(Schema, f'select channel_id from users where user= {user}') # => e
        ctx.memory.ask(f"What's the channel_id for {target_user}?") # => RAG
        ctx.memory.db.query(sql="") # SQL
        ctx.memory.get("channel_id") # point query

        # 长短期记忆
        #
        return obj

    @function
    def get_test_id1(
            self,
            ctx,
            user: str, # default from LLM
            c: Annotated[Schema, FromRAG(query="LLM"),
            d: Annotated[Schema, FromKV(key="channel_id"),
            e: Annotated[Schema, FromDB(sql="select channel_id from users where user= {user}"),
    ):
        """
        Get test id

        """
    # ...
    return None


async def main():
    async with agent.wrap(MyTool()) as tool:
        tool.use_hitl(ConsoleHandler())
        ctx = Context()
        ctx.bind(tool)
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
