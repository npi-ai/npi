from .context import Context

from playground.proto import playground_pb2


class ContextManager:
    """the manager of the context"""

    def __init__(self):
        self.threads = {}

    def new_thread(self, req: playground_pb2.ChatRequest) -> Context:
        """create a context"""
        th = Context(instruction=req.instruction)
        self.threads[th.id] = th
        return th

    def get_thread(self, tid: str) -> Context:
        """get a context by id"""
        return self.threads.get(tid)

    def release(self, tid: str) -> None:
        """delete a context by id"""
        del self.threads[tid]
