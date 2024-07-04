import asyncio
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import grpc
from google.protobuf.empty_pb2 import Empty

from npiai import agent_wrapper, AgentTool, BrowserAgentTool
from npiai.context import ContextManager, Context
from npiai.tools import GitHub, Gmail, GoogleCalendar
from npiai.tools.web import Chrome
from npiai.utils import logger
from npiai.error import UnauthorizedError

from playground.proto import (
    playground_pb2 as pb,
    playground_pb2_grpc as pbgrpc,
)


class Chat(pbgrpc.PlaygroundServicer):
    ctx_manager: ContextManager

    def __init__(self):
        self.ctx_manager = ContextManager()
        self.agent_container: Dict[pb.AppType, AgentTool] = {}

    async def start(self):
        self.agent_container[pb.GOOGLE_GMAIL] = agent_wrapper(Gmail())
        self.agent_container[pb.GOOGLE_CALENDAR] = agent_wrapper(GoogleCalendar())
        # self.agent_container[pb.TWITTER] = agent_wrapper(Twitter())
        # self.agent_container[pb.DISCORD] = agent_wrapper(Discord())
        self.agent_container[pb.GITHUB] = agent_wrapper(GitHub())
        self.agent_container[pb.WEB_BROWSER] = agent_wrapper(Chrome())
        # self.agent_container[pb.TWILIO] = agent_wrapper(Twilio())
        # self.agent_container[pb.SLACK] = agent_wrapper(Slack())

        for app in self.agent_container.values():
            await app.start()

    async def shutdown(self):
        for app in self.agent_container.values():
            await app.end()

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
                # ignore task result
                _ = asyncio.create_task(self.run(request.chat_request.type, ctx))
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

    async def run(self, app_type: pb.AppType, thread: Context):
        agent = None
        try:
            if app_type not in self.agent_container:
                raise ValueError(f"App {app_type} not found")
            agent = self.agent_container[app_type]
            thread.set_active_app(agent)
            result = await agent.chat(thread.instruction, thread)
            thread.finish(result)
        except UnauthorizedError as e:
            thread.failed(str(e))
        except Exception as e:
            err_msg = ''.join(traceback.format_exception(e))
            logger.error(err_msg)
            thread.failed(str(e))
            # raise e
        finally:
            thread.set_active_app(None)
            if isinstance(agent, BrowserAgentTool):
                # release current session
                await agent.goto_blank()


_cleanup_coroutines = []


async def serve(address: str) -> None:
    server = grpc.aio.server(ThreadPoolExecutor())
    srv = Chat()
    await srv.start()

    pbgrpc.add_PlaygroundServicer_to_server(srv, server)
    server.add_insecure_port(address)
    logger.info(f"Server serving at {address}")
    await server.start()

    # logger.info(f"Server serving at {address}")

    async def server_graceful_shutdown():
        logger.info("Starting graceful shutdown...")
        await srv.shutdown()
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


from dotenv import load_dotenv

if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(__file__), 'credentials/.env')
    load_dotenv(dotenv_path)
    main()
