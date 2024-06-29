import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor

import grpc
from google.protobuf.empty_pb2 import Empty

from npiai import agent_wrapper
from playground.context import ContextManager, Context
from npiai.app import Gmail, GoogleCalendar, GitHub, Twilio, Slack, Discord
from npiai.browser_app import Twitter, Browser
from npiai.utils import logger
from npiai.error import UnauthorizedError

from playground.proto import (
    playground_pb2 as pb,
    playground_pb2_grpc as pbgrpc
)


class Chat(pbgrpc.PlaygroundServicer):
    thread_manager: ContextManager

    def __init__(self):
        self.thread_manager = ContextManager()

    @staticmethod
    def get_app(app_type: pb.AppType):
        match app_type:
            case pb.GOOGLE_GMAIL:
                return Gmail()
            case pb.GOOGLE_CALENDAR:
                return GoogleCalendar()
            case pb.TWITTER:
                return Twitter()
            case pb.DISCORD:
                return Discord()
            case pb.GITHUB:
                return GitHub()
            case pb.WEB_BROWSER:
                return Browser()
            case pb.TWILIO:
                return Twilio()
            case pb.SLACK:
                return Slack()
            case _:
                raise Exception("unsupported application")

    async def Chat(
            self,
            request: pb.Request,
            _: grpc.ServicerContext,
    ) -> pb.Response:
        logger.info(f"received a request, code:[{request.code}], id: [{request.request_id}]")
        response = pb.Response()
        if request.code == pb.RequestCode.CHAT:
            try:
                thread = self.thread_manager.new_thread(request.chat_request)
                response.thread_id = thread.id
                response.code = pb.ResponseCode.SUCCESS
                # ignore task result
                _ = asyncio.create_task(self.run(thread))
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
        thread = self.thread_manager.get_thread(request.thread_id)

        if not thread:
            logger.error(f"context not found {request.thread_id}")
            resp = pb.GetAppScreenResponse()
            resp.code = pb.ResponseCode.FAILED
            return resp

        return pb.GetAppScreenResponse(base64=await thread.refresh_screenshot())

    async def __fetch_thread(self, req: pb.Request, resp: pb.Response):
        logger.info(f"fetching chat [{req.thread_id}]")
        thread = self.thread_manager.get_thread(req.thread_id)
        if not thread:
            logger.error("context not found")
            resp.code = pb.ResponseCode.FAILED
            return

        if thread.is_finished():
            resp.code = pb.ResponseCode.FINISHED
            resp.chat_response.message = thread.get_result()
            self.thread_manager.release(req.thread_id)
        elif thread.is_failed():
            resp.code = pb.ResponseCode.FAILED
            resp.chat_response.message = thread.get_failed_msg()
            self.thread_manager.release(req.thread_id)
        else:
            resp.code = pb.ResponseCode.MESSAGE
            cb = await thread.fetch_msg()
            if cb is None:
                if thread.is_finished():
                    resp.code = pb.ResponseCode.FINISHED
                    resp.chat_response.message = thread.get_result()
                    self.thread_manager.release(req.thread_id)
                elif thread.is_failed():
                    resp.code = pb.ResponseCode.FAILED
                    resp.chat_response.message = thread.get_failed_msg()
                    self.thread_manager.release(req.thread_id)
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
        thread = self.thread_manager.get_thread(req.thread_id)
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

    async def run(self, thread: Context):
        app = None
        try:
            app = self.get_app(thread.app_type)
            thread.set_active_app(app)
            await app.start()
            agent = agent_wrapper(app)
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
            if app is not None:
                # clean up
                await app.end()
            thread.set_active_app(None)


_cleanup_coroutines = []


async def serve(address: str) -> None:
    server = grpc.aio.server(ThreadPoolExecutor())
    pbgrpc.add_PlaygroundServicer_to_server(Chat(), server)
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


def main():
    try:
        asyncio.run(serve("[::]:9140"))
    finally:
        asyncio.run(*_cleanup_coroutines)


if __name__ == "__main__":
    main()
