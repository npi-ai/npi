import asyncio
import os
import json
import traceback
from concurrent.futures import ThreadPoolExecutor

import grpc
import uvicorn

from npiai_proto import api_pb2_grpc, api_pb2
from npi.core.thread import ThreadManager, Thread
from npi.app import google, discord, github
from npi.browser_app import twitter, general_browser_agent as browser
from npi.utils import logger
from npi.error.auth import UnauthorizedError


class Chat(api_pb2_grpc.AppServerServicer):
    thread_manager: ThreadManager

    def __init__(self):
        self.thread_manager = ThreadManager()

    @staticmethod
    def get_app(app_type: api_pb2.AppType):
        match app_type:
            case api_pb2.GOOGLE_GMAIL:
                return google.Gmail()
            case api_pb2.GOOGLE_CALENDAR:
                return google.GoogleCalendar()
            case api_pb2.TWITTER:
                return twitter.Twitter()
            case api_pb2.DISCORD:
                return discord.Discord()
            case api_pb2.GITHUB:
                return github.GitHub()
            case api_pb2.WEB_BROWSER:
                return browser.GeneralBrowserAgent()
            case _:
                raise Exception("unsupported application")

    async def Chat(
        self,
        request: api_pb2.Request,
        _: grpc.ServicerContext,
    ) -> api_pb2.Response:
        logger.info(f"received a request, code:[{request.code}], id: [{request.request_id}]")
        response = api_pb2.Response()
        if request.code == api_pb2.RequestCode.CHAT:
            try:
                thread = self.thread_manager.new_thread(request.chat_request)
                response.thread_id = thread.id
                response.code = api_pb2.ResponseCode.SUCCESS
                # await self.run(thread)
                # create background task
                asyncio.create_task(self.run(thread))
            except Exception as err:
                err_msg = ''.join(traceback.format_exception(err))
                print(err_msg)
                response.chat_response.message = err
                response.code = api_pb2.ResponseCode.FAILED
        elif request.code == api_pb2.RequestCode.FETCH:
            await self.__fetch_thread(request, response)
            response.thread_id = request.thread_id
        elif request.code == api_pb2.RequestCode.ACTION_RESULT:
            await self.__action(request, response)
            response.thread_id = request.thread_id
            response.code = api_pb2.ResponseCode.SUCCESS
        else:
            raise RuntimeError("Unknown request")
        response.request_id = request.request_id
        return response

    async def GetAppSchema(
        self,
        request: api_pb2.AppSchemaRequest,
        _: grpc.ServicerContext,
    ) -> api_pb2.AppSchemaResponse:
        try:
            app = self.get_app(request.type)
        except Exception as e:
            logger.error(''.join(traceback.format_exception(e)))
            raise e
        response = api_pb2.AppSchemaResponse()
        response.description = app.description
        schema = {
            "type": "function",
            "function": {
                "name": f"{app.name}",
                "description": f"{app.description}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": f"the task you want to do with tool {app.name}",
                        },
                    },
                    "required": ["message"],
                },
            },
        }
        response.schema = f"{json.dumps(schema)}"
        return response

    async def __fetch_thread(self, req: api_pb2.Request, resp: api_pb2.Response):
        logger.info(f"fetching chat [{req.thread_id}]")
        thread = self.thread_manager.get_thread(req.thread_id)
        if not thread:
            logger.error("thread not found")
            resp.code = api_pb2.ResponseCode.FAILED
            return

        if thread.is_finished():
            resp.code = api_pb2.ResponseCode.FINISHED
            resp.chat_response.message = thread.get_result()
            self.thread_manager.release(req.thread_id)
        elif thread.is_failed():
            resp.code = api_pb2.ResponseCode.FAILED
            resp.chat_response.message = thread.get_failed_msg()
            self.thread_manager.release(req.thread_id)
        else:
            resp.code = api_pb2.ResponseCode.MESSAGE
            cb = await thread.fetch_msg()
            if cb is None:
                if thread.is_finished():
                    resp.code = api_pb2.ResponseCode.FINISHED
                    resp.chat_response.message = thread.get_result()
                    self.thread_manager.release(req.thread_id)
                elif thread.is_failed():
                    resp.code = api_pb2.ResponseCode.FAILED
                    resp.chat_response.message = thread.get_failed_msg()
                    self.thread_manager.release(req.thread_id)
                else:
                    resp.code = api_pb2.ResponseCode.FAILED
                    resp.chat_response.message = "error in fetching message"
            else:
                resp.code = cb.type()
                if cb.type() == api_pb2.ResponseCode.ACTION_REQUIRED:
                    resp.action_response.CopyFrom(cb.client_response())
                    logger.info("action required")
                else:
                    resp.chat_response.message = cb.message()

    async def __action(self, req: api_pb2.Request, resp: api_pb2.Response):
        logger.info(f"received action chat [{req.thread_id}]")
        thread = self.thread_manager.get_thread(req.thread_id)
        if not thread:
            logger.error("thread not found")
            resp.code = api_pb2.ResponseCode.FAILED
            return

        cb = thread.get_callback(req.action_result_request.action_id)
        if not cb:
            logger.error("callback not found")
            resp.code = api_pb2.ResponseCode.FAILED
            resp.chat_response.message = "callback not found"
            return
        cb.callback(msg=req.action_result_request.action_result)

    async def run(self, thread: Thread):
        app = None
        try:
            app = self.get_app(thread.app_type)
            await app.start()
            result = await app.chat(thread.instruction, thread)
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
                await app.dispose()


_cleanup_coroutines = []


async def serve(address: str) -> None:
    server = grpc.aio.server(ThreadPoolExecutor())
    api_pb2_grpc.add_AppServerServicer_to_server(Chat(), server)
    server.add_insecure_port(address)
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


async def start():
    http_config = uvicorn.Config(
        "npi.server.auth:app",
        host="0.0.0.0",
        port=9141,
        reload=True
    )
    server = uvicorn.Server(http_config)
    server_task = asyncio.create_task(server.serve())

    await serve("[::]:9140")
    await server_task


def main():
    try:
        asyncio.run(start())
    finally:
        asyncio.run(*_cleanup_coroutines)


if __name__ == "__main__":
    main()
