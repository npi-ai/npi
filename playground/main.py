import asyncio
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
import base64
import json

import grpc
from google.protobuf.empty_pb2 import Empty
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

from npiai import agent_wrapper, AgentTool, BrowserAgentTool
from npiai.context import ContextManager, Context
from npiai.tools import GitHub, Gmail, GoogleCalendar, Twilio, Discord
from npiai.tools.web import Chromium, Twitter
from npiai.utils import logger
from npiai.error import UnauthorizedError

from playground.proto import (
    playground_pb2 as pb,
    playground_pb2_grpc as pbgrpc,
)

from playground.hitl import PlaygroundHITL


class Chat(pbgrpc.PlaygroundServicer):
    ctx_manager: ContextManager

    def __init__(self):
        self.ctx_manager = ContextManager()

    async def Chat(
            self,
            request: pb.Request,
            _: grpc.ServicerContext,
    ) -> pb.Response:
        logger.info(f"received a request, code:[{request.code}], id: [{request.request_id}]")
        response = pb.Response()
        if request.code == pb.RequestCode.CHAT:
            try:
                ctx = self.ctx_manager.new_thread(request.chat_request)
                response.thread_id = ctx.id
                response.code = pb.ResponseCode.SUCCESS
                decoded_bytes = base64.b64decode(request.authorization)
                _ = asyncio.create_task(self.run(request.chat_request.type, decoded_bytes.decode('utf-8'), ctx))
            except Exception as err:
                err_msg = ''.join(traceback.format_exception(err))
                print(err_msg)
                response.chat_response.message = err
                response.code = pb.ResponseCode.FAILED
        elif request.code == pb.RequestCode.FETCH:
            await self.__fetch_thread(request, response)
            response.thread_id = request.thread_id
        elif request.code == pb.RequestCode.ACTION_RESULT:
            await self.__action(request, response)
            response.thread_id = request.thread_id
            response.code = pb.ResponseCode.SUCCESS
        else:
            raise RuntimeError("Unknown request")
        response.request_id = request.request_id
        return response

    async def Ping(
            self,
            request: Empty,
            _: grpc.ServicerContext,
    ) -> Empty:
        return Empty()

    async def GetAppScreen(
            self,
            request: pb.GetAppScreenRequest,
            _: grpc.ServicerContext,
    ) -> pb.GetAppScreenResponse:
        thread = self.ctx_manager.get_thread(request.thread_id)

        if not thread:
            logger.error(f"context not found {request.thread_id}")
            resp = pb.GetAppScreenResponse()
            return resp

        return pb.GetAppScreenResponse(base64=await thread.refresh_screenshot())

    async def __fetch_thread(self, req: pb.Request, resp: pb.Response):
        logger.info(f"fetching chat [{req.thread_id}]")
        thread = self.ctx_manager.get_thread(req.thread_id)
        if not thread:
            logger.error("context not found")
            resp.code = pb.ResponseCode.FAILED
            return

        if thread.is_finished():
            resp.code = pb.ResponseCode.FINISHED
            resp.chat_response.message = thread.get_result()
            self.ctx_manager.release(req.thread_id)
        elif thread.is_failed():
            resp.code = pb.ResponseCode.FAILED
            resp.chat_response.message = thread.get_failed_msg()
            self.ctx_manager.release(req.thread_id)
        else:
            resp.code = pb.ResponseCode.MESSAGE
            cb = await thread.fetch_msg()
            if cb is None:
                if thread.is_finished():
                    resp.code = pb.ResponseCode.FINISHED
                    resp.chat_response.message = thread.get_result()
                    self.ctx_manager.release(req.thread_id)
                elif thread.is_failed():
                    resp.code = pb.ResponseCode.FAILED
                    resp.chat_response.message = thread.get_failed_msg()
                    self.ctx_manager.release(req.thread_id)
                else:
                    resp.code = pb.ResponseCode.FAILED
                    resp.chat_response.message = "error in fetching message"
            else:
                resp.code = cb.type()
                if cb.type() == pb.ResponseCode.ACTION_REQUIRED:
                    resp.action_response.CopyFrom(cb.client_response())
                    logger.info("action required")
                else:
                    resp.chat_response.message = cb.message()

    async def __action(self, req: pb.Request, resp: pb.Response):
        logger.info(f"received action chat [{req.thread_id}]")
        thread = self.ctx_manager.get_thread(req.thread_id)
        if not thread:
            logger.error("context not found")
            resp.code = pb.ResponseCode.FAILED
            return

        cb = thread.get_callback(req.action_result_request.action_id)
        if not cb:
            logger.error("callback not found")
            resp.code = pb.ResponseCode.FAILED
            resp.chat_response.message = "callback not found"
            return
        cb.callback(result=req.action_result_request)

    @staticmethod
    async def run(app_type: pb.AppType, authorization: str, ctx: Context):
        try:
            match app_type:
                case pb.AppType.GITHUB:
                    app = GitHub(access_token=authorization)
                case pb.AppType.DISCORD:
                    app = Discord(access_token=authorization)
                case pb.AppType.GOOGLE_GMAIL:
                    app = Gmail(
                        creds=Credentials.from_authorized_user_info(
                            info=json.loads(authorization),
                            scopes="https://mail.google.com/"
                        )
                    )
                case pb.AppType.GOOGLE_CALENDAR:
                    app = GoogleCalendar(
                        creds=Credentials.from_authorized_user_info(
                            info=json.loads(authorization),
                            scopes="https://www.googleapis.com/auth/calendar"
                        )
                    )
                case pb.AppType.TWITTER:
                    account = authorization.split(":")
                    app = Twitter(username=account[0], password=account[1])
                case pb.AppType.WEB_BROWSER:
                    app = Chromium()
                case pb.AppType.TWILIO:
                    account = authorization.split(":")
                    app = Twilio(
                        account_sid=account[0],
                        auth_token=account[1],
                        from_number=account[2]
                    )
                case _:
                    raise ValueError(f"Unsupported tool")
            agent = agent_wrapper(app)
            await agent.start(ctx)
            ctx.set_active_app(app)
            result = await agent.chat(ctx.instruction, ctx)
            await agent.end(ctx)
            ctx.finish(result)
        except UnauthorizedError as e:
            ctx.failed(str(e))
        except Exception as e:
            err_msg = ''.join(traceback.format_exception(e))
            logger.error(err_msg)
            ctx.failed(str(e))
            # raise e
        finally:
            ctx.set_active_app(None)


_cleanup_coroutines = []


async def serve(address: str) -> None:
    server = grpc.aio.server(ThreadPoolExecutor())
    srv = Chat()

    pbgrpc.add_PlaygroundServicer_to_server(srv, server)
    server.add_insecure_port(address)
    logger.info(f"Server serving at {address}")
    await server.start()

    # logger.info(f"Server serving at {address}")

    async def server_graceful_shutdown():
        logger.info("Starting graceful shutdown...")
        # Shuts down the server with 5 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)

    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


async def cleanup():
    if _cleanup_coroutines:
        logger.info("Cleaning up...")
        # Gather and run all cleanup coroutines
        await asyncio.gather(*[coro() for coro in _cleanup_coroutines])


def main():
    try:
        asyncio.run(serve("[::]:9140"))
    # except Exception as e:
    #     logger.error(f"Failed to start the server: {e}")
    finally:
        if _cleanup_coroutines:
            asyncio.run(cleanup())


if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(__file__), 'credentials/.env')
    load_dotenv(dotenv_path)
    main()
