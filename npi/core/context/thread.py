"""This module contains the classes for the thread and thread message"""
import datetime
import uuid
import json
from typing import List

from openai.types.chat import (
    ChatCompletionMessageParam, ChatCompletionFunctionCallOptionParam)


class ThreadMessage:
    """the message wrapper of a message in the thread"""
    thread_id: str
    agent_id: str
    task: str
    msg_id: str
    response: str
    messages:  List[ChatCompletionMessageParam]
    metadata: dict
    born_at: datetime.date  # RFC3339

    def __init__(self, agent_id: str, thread_id: str, task: str) -> None:
        self.agent_id = agent_id
        self.thread_id = thread_id
        self.task = task
        self.born_at = datetime.datetime.now()
        self.messages = []

    def append(self, msg: ChatCompletionMessageParam) -> None:
        """add a message to the thread"""
        self.messages.append(msg)

    def set_result(self, result: str) -> None:
        """set the result of the message"""
        self.response = result

    def raw(self) -> List[ChatCompletionMessageParam]:
        """return the raw message"""
        return self.messages.copy()

    def plaintext(self) -> str:
        """convert the thread message to plain text"""
        msgs = {
            "task": self.task,
            "response": self.response,
        }
        history = []
        for msg in self.messages:
            if isinstance(msg, dict):
                history.append(msg)
            elif msg.tool_calls:
                calls = []
                for tool_call in msg.tool_calls:
                    calls.append({
                        "id": tool_call.id,
                        "fn_name": tool_call.function.name,
                        "fn_arguments": json.loads(tool_call.function.arguments),
                    })
                history.append(calls)
            else:
                history.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        msgs['history'] = history
        return msgs


class Thread:
    """the abstraction of history management """
    agent_id: str
    id: str
    history: List[ThreadMessage | str]
    born_at: datetime.date

    def __init__(self) -> None:
        self.agent_id = 'default'
        self.id = str(uuid.uuid4())
        self.born_at = datetime.datetime.now()
        self.history = []

    def ask(self, msg: str) -> str:
        """retrieve the message from the thread"""
        return msg

    def append(self, msg: ThreadMessage) -> None:
        """add a message to the thread"""
        self.history.append(msg)

    def fork(self, task: str) -> ThreadMessage:
        """fork a child message, typically when call a new tools"""
        tm = ThreadMessage(agent_id=self.agent_id,
                           thread_id=self.id, task=task)
        self.history.append(tm)
        return tm

    def plaintext(self) -> str:
        """convert the thread to plain text"""
        msgs = []
        for msg in self.history:
            if isinstance(msg, ThreadMessage):
                return msg.plaintext()
            else:
                msgs.append(msg)

        return print(json.dumps(msgs))


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
        """delete a thread by id"""
        del self.threads[tid]
