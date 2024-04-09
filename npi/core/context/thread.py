"""This module contains the classes for the thread and thread message"""

from typing import List

from openai.types.chat import (ChatCompletionToolParam,)


class ThreadMessage:
    """the message wrapper of a message in the thread"""
    thread_id: str
    agent_id: str
    task: str
    msg_id: str
    response: str
    messages: List[ChatCompletionToolParam]
    metadata: dict
    born_at: str  # RFC3339

    def append(self, msg: List[ChatCompletionToolParam]) -> None:
        """add a message to the thread"""
        self.messages.append(msg)

    def set_result(self, result: str) -> None:
        """set the result of the message"""
        self.response = result


class Thread():
    """the abstraction of history management """
    id: str
    history: List[ThreadMessage]
    born_at: str  # RFC3339

    def __init__(self) -> None:
        pass

    def ask(self, msg: str) -> str:
        """retrieve the message from the thread"""
        return msg

    def append(self, msg: ThreadMessage) -> None:
        """add a message to the thread"""
        self.history.append(msg)

    def fork(self, task: str) -> ThreadMessage:
        """fork a child message, typically when call a new tools"""
        return ThreadMessage()

    def _to_plaintext(self) -> str:
        """convert the thread to plain text"""
        return '\n'.join([msg.msg_id for msg in self.history])


class ThreadManager():
    """the manager of the thread"""
    threads: dict

    def __init__(self):
        self.threads = {}

    def new_thread(self) -> Thread:
        """create a thread"""
        th = Thread()
        self.threads[th.id] = th
        return th

    def get_thread(self, tid: str) -> Thread:
        """get a thread by id"""
        return self.threads.get(tid)

    def delete_thread(self, tid: str) -> None:
        del self.threads[tid]
