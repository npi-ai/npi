import asyncio

import anthropic

from npiai import FunctionTool, function
from npiai.utils.test_utils import DebugContext
from npiai.integration.claude import get_claude_tools


class MyTool(FunctionTool):
    name = "Fibonacci"
    description = "My first NPi tool"

    def __init__(self):
        super().__init__()

    @function
    def fibonacci(self, n: int) -> int:
        """
        Get the nth Fibonacci number.

        Args:
            n: The index of the Fibonacci number in the sequence.
        """
        if n == 0:
            return 0
        if n == 1:
            return 1
        return self.fibonacci(n - 1) + self.fibonacci(n - 2)


async def main():
    async with MyTool() as tool:
        ctx = DebugContext()
        client = anthropic.Anthropic()
        messages = [
            {
                "role": "user",
                "content": "What's the 10-th fibonacci number?",
            }
        ]

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=messages,
            tools=get_claude_tools(tool),
        )

        for content in response.content:
            match content.type:
                case "text":
                    print(content.text)
                case "tool_use":
                    result = await tool.exec(ctx, content.name, content.input)
                    print(
                        f"Calling {content.name} with {content.input} returned {result}"
                    )


if __name__ == "__main__":
    asyncio.run(main())
