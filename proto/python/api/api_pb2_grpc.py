# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import api_pb2 as api_dot_api__pb2


class ChatServerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Chat = channel.stream_stream(
                '/npi.core.api.ChatServer/Chat',
                request_serializer=api_dot_api__pb2.ChatRequest.SerializeToString,
                response_deserializer=api_dot_api__pb2.ChatResponse.FromString,
                )


class ChatServerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Chat(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ChatServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Chat': grpc.stream_stream_rpc_method_handler(
                    servicer.Chat,
                    request_deserializer=api_dot_api__pb2.ChatRequest.FromString,
                    response_serializer=api_dot_api__pb2.ChatResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'npi.core.api.ChatServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ChatServer(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Chat(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/npi.core.api.ChatServer/Chat',
            api_dot_api__pb2.ChatRequest.SerializeToString,
            api_dot_api__pb2.ChatResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
