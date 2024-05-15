from typing_extensions import override

from openai import AssistantEventHandler, Client
from npiai.core.toolset import ToolSet


class EventHandler(AssistantEventHandler):
    def __init__(self, toolset: ToolSet, llm: Client, thread_id: str, stream_handler=None):
        super().__init__()
        self.toolset = toolset
        self.llm = llm
        self.thread_id = thread_id
        self.stream_handler = stream_handler

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
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": self.toolset.call(tool),
            })

        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with self.llm.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=self.thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                event_handler=EventHandler(self.toolset, self.llm, self.thread_id),
        ) as stream:
            self.stream_handler(run_id, stream)
