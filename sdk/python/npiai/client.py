from npiai.cdk import Tool
from npiai.tools.app import HelloWorld
from npiai.llm import LLM


class Client:
    def __init__(self, llm: LLM,
                 npi_api_key: str = "",
                 agent_mode: bool = False,
                 server_endpoint: str = "localhost:9140",
                 ):
        self.server_endpoint = server_endpoint
        self.npi_api_key = npi_api_key
        self.agent_mode = agent_mode
        self.llm = llm

    def Example(self, **kwargs) -> Tool:
        return HelloWorld(
            agent_mode=kwargs.get("agent_mode", self.agent_mode),
            model=kwargs.get("model", self.llm.default_model()),
            server_mode=False,
            llm=self.llm,
        )

    def Gmail(self, **kwargs) -> Tool:
        # remove later
        return HelloWorld(
            agent_mode=kwargs.get("agent_mode", self.agent_mode),
            model=kwargs.get("model", self.llm.default_model()),
            server_mode=False,
            llm=self.llm,
        )

    def GoogleCalender(self, **kwargs) -> Tool:
        # remove later
        return HelloWorld(
            agent_mode=kwargs.get("agent_mode", self.agent_mode),
            model=kwargs.get("model", self.llm.default_model()),
            server_mode=False,
            llm=self.llm,
        )

    def GitHub(self, **kwargs) -> Tool:
        # remove later
        return HelloWorld(
            agent_mode=kwargs.get("agent_mode", self.agent_mode),
            model=kwargs.get("model", self.llm.default_model()),
            server_mode=False,
            llm=self.llm,
        )
