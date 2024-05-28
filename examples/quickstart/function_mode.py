import os

from openai import OpenAI
from npiai import app, NPi

npi = NPi()


@npi.function(description='demo')
def test():
    return 'Hello NPi!'


if __name__ == "__main__":
    time_tools = app.time.create()
    print(time_tools.name)  # => time
    npi.add(time_tools)
    print(
        npi.debug_sync(
            toolset=time_tools.name,
            fn_name='get_timezone',
            args={
                'test': 'Shanghai',
                'cases': ['case1', 'case2'],
            },
        )
    )

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    messages = [
        {
            "role": "user",
            "content": "What day is it today?",
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=npi.tools,  # use npi as a tool package
        tool_choice="auto",
        max_tokens=4096,
    )
    response_message = response.choices[0].message

    messages.append(response_message)

    print(npi.call_sync(response_message.tool_calls))
