from .thread import Thread

from npiai_proto import api_pb2


class ThreadManager:
    """the manager of the thread"""

    def __init__(self):
        self.threads = {}

    def new_thread(self, req: api_pb2.ChatRequest) -> Thread:
        """create a thread"""
        th = Thread(app_type=req.type, instruction=req.instruction)
        self.threads[th.id] = th
        return th

    def get_thread(self, tid: str) -> Thread:
        """get a thread by id"""
        return self.threads.get(tid)

    def release(self, tid: str) -> None:
        """delete a thread by id"""
        del self.threads[tid]
