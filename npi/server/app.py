import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

import grpc

from proto.python.api import api_pb2_grpc, api_pb2
from npi.app import google
from npi.core.context import Thread


class Chat(api_pb2_grpc.ChatServerServicer):

    def Chat(
            self,
            request_iterator: Iterable[api_pb2.ChatRequest],
            context: grpc.ServicerContext,
    ) -> Iterable[api_pb2.ChatResponse]:
        try:
            request = next(request_iterator)
            logging.info(
                "Received a phone call request for number [%s]",
                request.instruction,
            )
        except StopIteration:
            raise RuntimeError("Failed to receive call request")
        response = api_pb2.ChatResponse()
        response.request_id = request.request_id

        if request.app_type == api_pb2.GOOGLE_GMAIL:
            gmail = google.Gmail()
        elif request.app_type == api_pb2.GOOGLE_CALENDAR:
            gc = google.GoogleCalendar()
            msg = gc.chat(message=request.instruction, thread=Thread())
            response.message = msg
        else:
            response.type = api_pb2.APP_UNSUPPORTED
            response.message = "Error: App not found"
        return iter([response])


def serve(address: str) -> None:
    server = grpc.server(ThreadPoolExecutor())

    api_pb2_grpc.add_ChatServerServicer_to_server(Chat(), server)
    server.add_insecure_port(address)
    server.start()
    logging.info("Server serving at %s", address)
    server.wait_for_termination()


def main():
    logging.basicConfig(level=logging.INFO)
    serve("[::]:9140")


if __name__ == "__main__":
    main()
