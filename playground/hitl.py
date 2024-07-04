from npiai import HITL
from npiai.context import Context
from npiai.core import callback
from playground.proto import playground_pb2


class PlaygroundHITL(HITL):
    async def confirm(self, ctx: Context, app_name: str, message: str) -> bool:
        cb = callback.Callable(
            action=playground_pb2.ActionRequiredResponse(
                type=playground_pb2.ActionType.CONFIRMATION,
                message=f'[{app_name}]: {message}'
            )
        )
        cb.action.action_id = cb.id()

        await ctx.send_msg(cb)
        res = await cb.wait()

        return res.is_approved()

    async def input(self, ctx: Context, app_name: str, message: str) -> str:
        cb = callback.Callable(
            action=playground_pb2.ActionRequiredResponse(
                type=playground_pb2.ActionType.INFORMATION,
                message=f'[{app_name}]: {message}'
            )
        )
        cb.action.action_id = cb.id()

        await ctx.send_msg(cb)
        res = await cb.wait()

        return res.result.action_result
