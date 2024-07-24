# NPI

> [!WARNING]
> NPi is currently under active development and the APIs are subject to change in the future release. It is recommended
> to use the command line tool to try it out.

NPi is an open-source platform providing **_Tool-use_** APIs to empower AI agents with the ability to take action in virtual world!

[🛠️Try NPi Online](https://try.npi.ai): Try NPi on online Playground

[👀 NPi Example](https://www.npi.ai/docs/examples?utm_source=github&utm_campaign=readme): **Highly recommended to check this first** - See what you can build with NPi.

[🔥 Introducing NPi](https://www.npi.ai/blog/introducing-npi?utm_source=github&utm_campaign=readme): Why we build NPi?

[📚 NPi Documentation](https://www.npi.ai/docs?utm_source=github&utm_campaign=readme): How to use NPi?

[📢 Join our community on Discord](https://discord.gg/wdskUcKc): Let's build NPi together 👻 !


NPi (**N**atural-language **P**rogramming **I**nterface), pronounced as **"N π"**, is an open-source platform providing **_Tool-use_** APIs to empower AI agents with the ability to operate and interact with a diverse array of software tools and applications.

<nav className="text-center my-4">
  [Getting Started](/docs)
  |
  [Examples](/examples)
  |
  [NPi Cloud(coming soon)](#)
</nav>

## Installation

```sh
pip install npiai
```

## One-Minute Quick Start

Let's create a new tool to compute the nth Fibonacci number. Start by crafting a new Python file titled `main.py` and insert the following snippet:

```py filename="main.py" showLineNumbers {9,12-13,19-22,33,44,51}
import os
import json
import asyncio

from openai import OpenAI
from npiai import FunctionTool, function


class MyTool(FunctionTool):
    def __init__(self):
        super().__init__(
            name='Fibonacci',
            description='My first NPi tool',
        )

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
        print(f'The schema of the tool is\n\n {json.dumps(tool.tools, indent=2)}')
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        messages = [
            {
                "role": "user",
                "content": "What's the 10-th fibonacci number?",
            }
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tool.tools,  # use tool as functions package
            tool_choice="auto",
            max_tokens=4096,
        )
        response_message = response.choices[0].message
        if response_message.tool_calls:
            result = await tool.call(tool_calls=response_message.tool_calls)
            print(f'The result of function\n\n {json.dumps(result, indent=2)}')


if __name__ == "__main__":
    asyncio.run(main())
```

Now, run the tool:

```sh
python main.py
```

You will see the function result in [OpenAI function calling format](https://platform.openai.com/docs/guides/function-calling/function-calling):

```json {6}
[
  {
    "role": "tool",
    "name": "fibonacci",
    "tool_call_id": "call_4KItpriZmoGxXgDloI5WOtHm",
    "content": 55
  }
]
```

`content: 55` is the result of function calling, and the schema：

```json {6, 9-12}
[
  {
    "type": "function",
    "function": {
      "name": "fibonacci",
      "description": "Get the nth Fibonacci number.",
      "parameters": {
        "properties": {
          "n": {
            "description": "The index of the Fibonacci number in the sequence.",
            "type": "integer"
          }
        },
        "required": [
          "n"
        ],
        "type": "object"
      }
    }
  }
]
```

That's it! You've successfully created and run your first NPi tool. 🎉

## Next Steps

- [Read the Documentation](https://www.npi.ai/docs)
- [Explore More Examples](https://www.npi.ai/examples)
- [NPi Cloud(coming soon)](#)

## License

Apache License 2.0
