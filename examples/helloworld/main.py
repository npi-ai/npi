from npiai import NPI, group
from npiai import OpenAI as OpenAIWrapper
from openai import OpenAI

if __name__ == '__main__':
    # 1. Function Mode
    llm = OpenAIWrapper(api_key="abcd", model="gpt-4o")
    client = NPI(llm=llm)

    gh = client.GitHub()
    oai = OpenAI()
    messages = [
        {
            "role": "system",
            "content": "Hello, how can I help you today?",
        },
        {
            "role": "user",
            "content": "Hello",
        }
    ]
    response = oai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=[gh.schema()],
        tool_choice="auto",
        max_tokens=4096,
    )
    response_message = response.choices[0].message

    messages.append(response_message)

    tool_calls = response_message.tool_calls

    for tool_call in tool_calls:
        gh.call(tool_call)

    # 2. Agent Mode
    gh = client.GitHub(agent_mode=True, model="gpt-4o")
    gh.chat("how many stars does numpy have?")

    # 3. group multiple tools
    gm = client.Gmail()
    new_tool = group(tools=[gh, gm], agent_mode=True)
    print(new_tool.schema())
    print(new_tool.chat("abaaba"))
