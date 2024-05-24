from npiai import Client

from openai.types.chat import ChatCompletionMessage

if __name__ == '__main__':
    client = Client(
        server_endpoint="localhost",
        api_key="",
        agent_mode=False,
        llm=None,
    )
    tool = client.Example()
    print(tool.chat("world"))
