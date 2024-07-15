from .context import Context


class ContextManager:
    """the manager of the context"""

    def __init__(self):
        self.threads = {}

    def new_thread(self, req) -> Context:
        """create a context"""
        th = Context()
        self.threads[th.id] = th
        return th

    def get_thread(self, tid: str) -> Context:
        """get a context by id"""
        return self.threads.get(tid)

    def release(self, tid: str) -> None:
        """delete a context by id"""
        del self.threads[tid]
