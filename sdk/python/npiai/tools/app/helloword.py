from npiai.cdk import Tool, function
from npiai.llm import LLM


# @Tool
class HelloWorld(Tool):
    def __init__(self,
                 llm: LLM,
                 agent_mode: bool,
                 server_mode: bool,
                 server_endpoint: str = "localhost:9140",
                 run_port: int = 19410,
                 ):
        super().__init__(
            llm=llm,
            name="helloworld",
            version="20240523",
            description="Example tool",
            author="npiai",
            agent_mode=agent_mode,
            server_mode=server_mode,
            server_endpoint=server_endpoint,
            run_port=run_port,
        )

    @function(
        name="hello",
        method="get/post",
        description="Say hello",
    )
    def hello(self, msg: str) -> str:
        return f"Hello {msg}!"

    def chat(self, msg: str) -> str:
        return f"Echo: {msg}"
