import * as grpcWeb from 'grpc-web';

import * as google_protobuf_empty_pb from 'google-protobuf/google/protobuf/empty_pb'; // proto import: "google/protobuf/empty.proto"
import * as api_pb from './api_pb'; // proto import: "api.proto"


export class AppServerClient {
  constructor (hostname: string,
               credentials?: null | { [index: string]: string; },
               options?: null | { [index: string]: any; });

  chat(
    request: api_pb.Request,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
               response: api_pb.Response) => void
  ): grpcWeb.ClientReadableStream<api_pb.Response>;

  getAppSchema(
    request: api_pb.AppSchemaRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
               response: api_pb.AppSchemaResponse) => void
  ): grpcWeb.ClientReadableStream<api_pb.AppSchemaResponse>;

  authorize(
    request: api_pb.AuthorizeRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
               response: api_pb.AuthorizeResponse) => void
  ): grpcWeb.ClientReadableStream<api_pb.AuthorizeResponse>;

  googleAuthCallback(
    request: api_pb.AuthorizeRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
               response: google_protobuf_empty_pb.Empty) => void
  ): grpcWeb.ClientReadableStream<google_protobuf_empty_pb.Empty>;

  ping(
    request: google_protobuf_empty_pb.Empty,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
               response: google_protobuf_empty_pb.Empty) => void
  ): grpcWeb.ClientReadableStream<google_protobuf_empty_pb.Empty>;

}

export class AppServerPromiseClient {
  constructor (hostname: string,
               credentials?: null | { [index: string]: string; },
               options?: null | { [index: string]: any; });

  chat(
    request: api_pb.Request,
    metadata?: grpcWeb.Metadata
  ): Promise<api_pb.Response>;

  getAppSchema(
    request: api_pb.AppSchemaRequest,
    metadata?: grpcWeb.Metadata
  ): Promise<api_pb.AppSchemaResponse>;

  authorize(
    request: api_pb.AuthorizeRequest,
    metadata?: grpcWeb.Metadata
  ): Promise<api_pb.AuthorizeResponse>;

  googleAuthCallback(
    request: api_pb.AuthorizeRequest,
    metadata?: grpcWeb.Metadata
  ): Promise<google_protobuf_empty_pb.Empty>;

  ping(
    request: google_protobuf_empty_pb.Empty,
    metadata?: grpcWeb.Metadata
  ): Promise<google_protobuf_empty_pb.Empty>;

}

