import time


class Callable:
    msg: str
    fn: callable
    called: bool

    def __init__(self, msg: str, fn=None):
        self.fn = fn
        self.msg = msg
        self.called = False

    def message(self) -> str:
        return self.msg

    def callback(self, **kwargs):
        if self.fn:
            self.fn(**kwargs)
        self.called = True

    def wait(self):
        while not self.called:
            time.sleep(0.001)
        return

