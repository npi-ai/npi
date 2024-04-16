import logging
import asyncio

from concurrent.futures import ThreadPoolExecutor

import grpc

from proto.python.api import api_pb2_grpc, api_pb2
from npi.core.thread import ThreadManager, Thread
from npi.app import google


class Chat(api_pb2_grpc.ChatServerServicer):
    thread_manager: ThreadManager

    def __init__(self):
        self.thread_manager = ThreadManager()

    async def Chat(
            self,
            request: api_pb2.Request,
            context: grpc.ServicerContext,
    ) -> api_pb2.Response:
        logging.info("received a request, code:[%s], ", request.code)
        response = api_pb2.Response()
        if request.code == api_pb2.RequestCode.CHAT:
            try:
                thread = self.thread_manager.new_thread(request.chat_request)
                response.thread_id = thread.id
                response.code = api_pb2.ResponseCode.MESSAGE
                Chat.run(thread)
            except Exception as e:
                logging.error("error in chat: %s", e)
                response.code = api_pb2.ResponseCode.ERROR
        elif request.code == api_pb2.RequestCode.FETCH:
            await self.__fetch_thread(request, response)
            response.thread_id = request.thread_id
        elif request.code == api_pb2.RequestCode.ACTION_RESULT:
            pass
        else:
            raise RuntimeError("Unknown request")
        response.request_id = request.request_id
        return response

    async def __fetch_thread(self, req: api_pb2.Request, resp: api_pb2.Response):
        logging.info("fetching chat [%s]", req.thread_id)
        thread = self.thread_manager.get_thread(req.thread_id)
        if not thread:
            logging.error("thread not found")
            resp.code = api_pb2.ResponseCode.ERROR
            return

        if thread.is_finished():
            resp.code = api_pb2.ResponseCode.SUCCESS
            resp.chat_response.message = thread.get_result()
            self.thread_manager.release(req.thread_id)
        else:
            resp.code = api_pb2.ResponseCode.MESSAGE
            cb = await thread.fetch_msg()
            if cb is None:
                if thread.is_finished():
                    resp.code = api_pb2.ResponseCode.SUCCESS
                    resp.chat_response.message = thread.get_result()
                    self.thread_manager.release(req.thread_id)
                else:
                    resp.code = api_pb2.ResponseCode.FAILED
                    resp.chat_response.message = "error in fetching message"
            else:
                print(cb.message)
                resp.chat_response.message = cb.message()

    @staticmethod
    def run(thread: Thread):
        if thread.app_type == api_pb2.GOOGLE_CALENDAR:
            gc = google.GoogleCalendar()
            asyncio.create_task(gc.chat(thread.instruction, thread))
        else:
            raise Exception("unsupported application")


_cleanup_coroutines = []


async def serve(address: str) -> None:
    server = grpc.aio.server(ThreadPoolExecutor())
    api_pb2_grpc.add_ChatServerServicer_to_server(Chat(), server)
    server.add_insecure_port(address)
    await server.start()
    logging.info("Server serving at %s", address)

    async def server_graceful_shutdown():
        logging.info("Starting graceful shutdown...")
        # Shuts down the server with 5 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)

    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(serve("[::]:9140"))
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()


if __name__ == "__main__":
    main()
