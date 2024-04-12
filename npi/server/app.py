import threading
import logging
import asyncio

from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

import grpc

from proto.python.api import api_pb2_grpc, api_pb2
from npi.app import google
from npi.core.context import Thread


class Chat(api_pb2_grpc.ChatServerServicer):

    async def Chat(
            self,
            request: api_pb2.Request,
            context: grpc.ServicerContext,
    ) -> api_pb2.Response:
        logging.info(
            "received a request [%s]",
            request.code,
        )
        response = api_pb2.Response()
        response.request_id = request.request_id
        if request.code == api_pb2.RequestCode.CHAT:
            pass
        elif request.code == api_pb2.RequestCode.FETCH:
            pass
        elif request.code == api_pb2.RequestCode.ACTION_RESULT:
            pass
        else:
            raise RuntimeError("Unknown request")
        return response


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


async def test0():
    gc = google.GoogleCalendar()
    thread = Thread()
    tasks = [listen(thread), gc.chat("is ww@lifecycle.sh available tomorrow", thread)]
    await asyncio.gather(*tasks)


async def listen(thread: Thread):
    while True:
        try:
            cb = await thread.receive_msg()
            print("cb -> ", cb.message())
            if cb.message() == "done":
                break
        except asyncio.QueueEmpty:  # Replace with the specific exception if different
            await asyncio.sleep(1)

if __name__ == "__main__":
    main()
