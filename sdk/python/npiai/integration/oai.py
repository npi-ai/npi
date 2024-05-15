from typing_extensions import override
import json

from openai import AssistantEventHandler, Client
from npiai.core.toolset import ToolSet


class EventHandler(AssistantEventHandler):
    def __init__(self, toolset: ToolSet):
        super().__init__()
        self.toolset = toolset
        # self.llm = llm

    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data, run_id):
        tool_outputs = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            js = json.loads(tool.function.arguments)
            if tool.function.name == "gmail":
                resp = self.npi_tools["gmail"].chat(js['message'])
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": resp,
                })

        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=self.current_run.thread_id,
                run_id=self.current_run.id,
                tool_outputs=tool_outputs,
                event_handler=self,
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
            print()
