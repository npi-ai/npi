import uuid
from typing import Literal

from npiai import HITL
from npiai.types.runtime_message import HITLMessage
from ._context import CloudContext


class CloudHITL(HITL):
    @staticmethod
    async def _send_action(
        ctx: CloudContext, action: Literal["input", "confirm"], message: str
    ) -> str | None:
        action_id = str(uuid.uuid4())

        msg: HITLMessage = {
            "type": "hitl",
            "action": action,
            "id": action_id,
            "message": message,
        }

        await ctx.send(msg)

        result = await ctx.receive_action_result(action_id)
        return result

    async def confirm(self, ctx: CloudContext, app_name: str, message: str) -> bool:
        res = await self._send_action(
            ctx=ctx,
            action="confirm",
            message=f"[{app_name}]: {message}",
        )

        return res.lower() == "approved"

    async def input(self, ctx: CloudContext, app_name: str, message: str) -> str:
        res = await self._send_action(
            ctx=ctx,
            action="input",
            message=f"[{app_name}]: {message}",
        )

        return res
