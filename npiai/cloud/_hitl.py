import uuid
from typing import Literal, List

from npiai import HITL
from npiai.types.runtime_message import HITLMessage
from ._context import CloudContext


class CloudHITL(HITL):
    @staticmethod
    async def _send_action(
        ctx: CloudContext,
        action: Literal["input", "confirm", "select"],
        message: str,
        default: str | bool,
        choices: List[str] = None,
    ) -> str | None:
        action_id = str(uuid.uuid4())

        msg: HITLMessage = {
            "type": "hitl",
            "action": action,
            "id": action_id,
            "message": message,
            "default": default,
        }

        if action == "select":
            msg["choices"] = choices

        await ctx.send(msg)

        result = await ctx.receive_action_result(action_id)
        return result

    async def confirm(
        self,
        ctx: CloudContext,
        tool_name: str,
        message: str,
        default=False,
    ) -> bool:
        res = await self._send_action(
            ctx=ctx,
            action="confirm",
            message=f"[{tool_name}]: {message}",
            default=default,
        )

        return res.lower() == "approved"

    async def input(
        self,
        ctx: CloudContext,
        tool_name: str,
        message: str,
        default="",
    ) -> str:
        res = await self._send_action(
            ctx=ctx,
            action="input",
            message=f"[{tool_name}]: {message}",
            default=default,
        )

        return res

    async def select(
        self,
        ctx: CloudContext,
        tool_name: str,
        message: str,
        choices: List[str],
        default="",
    ):
        res = await self._send_action(
            ctx=ctx,
            action="select",
            message=f"[{tool_name}]: {message}",
            default=default,
            choices=choices,
        )

        return res
