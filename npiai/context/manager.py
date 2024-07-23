from fastapi import Request

from .context import Context


class ContextManager:
    """the manager of the context"""

    def __init__(self):
        self.contexts = {}

    def from_request(self, req: Request) -> Context:
        """create a context"""
        ctx = Context(req=req)
        self.contexts[ctx.id] = ctx
        return ctx

    def get_thread(self, tid: str) -> Context:
        """get a context by id"""
        return self.threads.get(tid)

    def release(self, tid: str) -> None:
        """delete a context by id"""
        del self.threads[tid]
