from .context import Context


class ContextManager:
    """the manager of the context"""

    def __init__(self):
        self.contexts = {}

    def get_context(self, ssid: str) -> Context | None:
        return self.contexts.get(ssid, None)

    def save_context(self, ctx: Context):
        self.contexts[ctx.id] = ctx

    def release(self, tid: str) -> None:
        """delete a context by id"""
        del self.contexts[tid]
