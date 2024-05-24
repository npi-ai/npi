import os
import socket
import uuid
from typing import List

import grpc

from npiai.llm import LLM
from npiai_proto.controller_pb2_grpc import ControllerStub
from npiai_proto.controller_pb2 import (
    RegisterToolRequest,
    ToolSpec, Metadata, FunctionSpec, Runtime, Function, PYTHON
)


def function(name: str, method: str):
    pass


class Tool:
    def __init__(self, name: str,
                 llm: LLM,
                 version: str,
                 description: str,
                 author: str,
                 agent_mode: bool,
                 server_mode: bool,
                 server_endpoint: str = "localhost:9140",
                 run_port: int = 19410,
                 ):
        self.llm = llm
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.agent_mode = agent_mode
        self.server_mode = server_mode
        self.server_endpoint = server_endpoint
        self.run_port = run_port
        self.id = uuid.uuid4()
        if server_mode:
            self.token = ''
            self.channel = grpc.insecure_channel(server_endpoint)
            self.controller_stub = ControllerStub(self.channel)
            self.__register_to_controller()
            # TODO start heartbeat task
            # TODO watch exit signal and unregister
            self.start()

    def start(self):
        pass

    def stop(self):
        pass

    def schema(self):
        pass

    def call(self, request):
        pass

    def chat(self, msg: str) -> str:
        pass

    def __register_to_controller(self):
        resp = self.controller_stub.RegisterTool(request=RegisterToolRequest(
            tool=self.__tool_spec(),
            hostname=socket.gethostname(),
            ip=socket.gethostbyname(socket.gethostname()),
            port=self.run_port,
        ))
        self.token = resp.token

    def __tool_spec(self) -> ToolSpec:
        return ToolSpec(
            metadata=Metadata(
                id=str(self.id),
                name=self.name,
                version=self.version,
                description=self.description,
                author=self.author,
                agent_mode=self.agent_mode,
            ),
            function_spec=FunctionSpec(
                runtime=Runtime(
                    language=PYTHON,
                    version=os.getenv('NPI_RUNTIME_PYTHON_VERSION', '3.12'),
                    image=os.getenv('NPI_RUNTIME_IMAGE', 'N/a'),
                ),
                dependencies=[],  # optional for provisioned tools
                functions=self.__get_functions(),
            ),
        )

    def __get_functions(self) -> List[Function]:
        pass

    def __str__(self):
        return f"Tool: {self.name}"


def group(tools: List[Tool],
          name: str = "",
          agent_mode: bool = False,
          version: str = "",
          description: str = "",
          author: str = "",
          server_mode: bool = False,
          server_endpoint: str = "localhost:9140",
          run_port: int = 19410,
          ) -> Tool:
    pass
