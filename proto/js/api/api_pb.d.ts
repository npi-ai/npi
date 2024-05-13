import * as jspb from 'google-protobuf'

import * as google_protobuf_empty_pb from 'google-protobuf/google/protobuf/empty_pb'; // proto import: "google/protobuf/empty.proto"


export class Request extends jspb.Message {
  getCode(): RequestCode;
  setCode(value: RequestCode): Request;

  getRequestId(): string;
  setRequestId(value: string): Request;

  getThreadId(): string;
  setThreadId(value: string): Request;

  getChatRequest(): ChatRequest | undefined;
  setChatRequest(value?: ChatRequest): Request;
  hasChatRequest(): boolean;
  clearChatRequest(): Request;

  getActionResultRequest(): ActionResultRequest | undefined;
  setActionResultRequest(value?: ActionResultRequest): Request;
  hasActionResultRequest(): boolean;
  clearActionResultRequest(): Request;

  getEmpty(): google_protobuf_empty_pb.Empty | undefined;
  setEmpty(value?: google_protobuf_empty_pb.Empty): Request;
  hasEmpty(): boolean;
  clearEmpty(): Request;

  getRequestCase(): Request.RequestCase;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): Request.AsObject;
  static toObject(includeInstance: boolean, msg: Request): Request.AsObject;
  static serializeBinaryToWriter(message: Request, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): Request;
  static deserializeBinaryFromReader(message: Request, reader: jspb.BinaryReader): Request;
}

export namespace Request {
  export type AsObject = {
    code: RequestCode,
    requestId: string,
    threadId: string,
    chatRequest?: ChatRequest.AsObject,
    actionResultRequest?: ActionResultRequest.AsObject,
    empty?: google_protobuf_empty_pb.Empty.AsObject,
  }

  export enum RequestCase { 
    REQUEST_NOT_SET = 0,
    CHAT_REQUEST = 10,
    ACTION_RESULT_REQUEST = 12,
    EMPTY = 99,
  }
}

export class AppSchemaRequest extends jspb.Message {
  getType(): AppType;
  setType(value: AppType): AppSchemaRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): AppSchemaRequest.AsObject;
  static toObject(includeInstance: boolean, msg: AppSchemaRequest): AppSchemaRequest.AsObject;
  static serializeBinaryToWriter(message: AppSchemaRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): AppSchemaRequest;
  static deserializeBinaryFromReader(message: AppSchemaRequest, reader: jspb.BinaryReader): AppSchemaRequest;
}

export namespace AppSchemaRequest {
  export type AsObject = {
    type: AppType,
  }
}

export class AppSchemaResponse extends jspb.Message {
  getSchema(): string;
  setSchema(value: string): AppSchemaResponse;

  getDescription(): string;
  setDescription(value: string): AppSchemaResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): AppSchemaResponse.AsObject;
  static toObject(includeInstance: boolean, msg: AppSchemaResponse): AppSchemaResponse.AsObject;
  static serializeBinaryToWriter(message: AppSchemaResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): AppSchemaResponse;
  static deserializeBinaryFromReader(message: AppSchemaResponse, reader: jspb.BinaryReader): AppSchemaResponse;
}

export namespace AppSchemaResponse {
  export type AsObject = {
    schema: string,
    description: string,
  }
}

export class ChatRequest extends jspb.Message {
  getType(): AppType;
  setType(value: AppType): ChatRequest;

  getInstruction(): string;
  setInstruction(value: string): ChatRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ChatRequest.AsObject;
  static toObject(includeInstance: boolean, msg: ChatRequest): ChatRequest.AsObject;
  static serializeBinaryToWriter(message: ChatRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ChatRequest;
  static deserializeBinaryFromReader(message: ChatRequest, reader: jspb.BinaryReader): ChatRequest;
}

export namespace ChatRequest {
  export type AsObject = {
    type: AppType,
    instruction: string,
  }
}

export class ActionResultRequest extends jspb.Message {
  getActionId(): string;
  setActionId(value: string): ActionResultRequest;

  getActionResult(): string;
  setActionResult(value: string): ActionResultRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ActionResultRequest.AsObject;
  static toObject(includeInstance: boolean, msg: ActionResultRequest): ActionResultRequest.AsObject;
  static serializeBinaryToWriter(message: ActionResultRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ActionResultRequest;
  static deserializeBinaryFromReader(message: ActionResultRequest, reader: jspb.BinaryReader): ActionResultRequest;
}

export namespace ActionResultRequest {
  export type AsObject = {
    actionId: string,
    actionResult: string,
  }
}

export class AuthorizeRequest extends jspb.Message {
  getType(): AppType;
  setType(value: AppType): AuthorizeRequest;

  getCredentialsMap(): jspb.Map<string, string>;
  clearCredentialsMap(): AuthorizeRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): AuthorizeRequest.AsObject;
  static toObject(includeInstance: boolean, msg: AuthorizeRequest): AuthorizeRequest.AsObject;
  static serializeBinaryToWriter(message: AuthorizeRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): AuthorizeRequest;
  static deserializeBinaryFromReader(message: AuthorizeRequest, reader: jspb.BinaryReader): AuthorizeRequest;
}

export namespace AuthorizeRequest {
  export type AsObject = {
    type: AppType,
    credentialsMap: Array<[string, string]>,
  }
}

export class AuthorizeResponse extends jspb.Message {
  getResultMap(): jspb.Map<string, string>;
  clearResultMap(): AuthorizeResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): AuthorizeResponse.AsObject;
  static toObject(includeInstance: boolean, msg: AuthorizeResponse): AuthorizeResponse.AsObject;
  static serializeBinaryToWriter(message: AuthorizeResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): AuthorizeResponse;
  static deserializeBinaryFromReader(message: AuthorizeResponse, reader: jspb.BinaryReader): AuthorizeResponse;
}

export namespace AuthorizeResponse {
  export type AsObject = {
    resultMap: Array<[string, string]>,
  }
}

export class Response extends jspb.Message {
  getCode(): ResponseCode;
  setCode(value: ResponseCode): Response;

  getRequestId(): string;
  setRequestId(value: string): Response;

  getThreadId(): string;
  setThreadId(value: string): Response;

  getChatResponse(): ChatResponse | undefined;
  setChatResponse(value?: ChatResponse): Response;
  hasChatResponse(): boolean;
  clearChatResponse(): Response;

  getActionResponse(): ActionRequiredResponse | undefined;
  setActionResponse(value?: ActionRequiredResponse): Response;
  hasActionResponse(): boolean;
  clearActionResponse(): Response;

  getEmpty(): google_protobuf_empty_pb.Empty | undefined;
  setEmpty(value?: google_protobuf_empty_pb.Empty): Response;
  hasEmpty(): boolean;
  clearEmpty(): Response;

  getResponseCase(): Response.ResponseCase;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): Response.AsObject;
  static toObject(includeInstance: boolean, msg: Response): Response.AsObject;
  static serializeBinaryToWriter(message: Response, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): Response;
  static deserializeBinaryFromReader(message: Response, reader: jspb.BinaryReader): Response;
}

export namespace Response {
  export type AsObject = {
    code: ResponseCode,
    requestId: string,
    threadId: string,
    chatResponse?: ChatResponse.AsObject,
    actionResponse?: ActionRequiredResponse.AsObject,
    empty?: google_protobuf_empty_pb.Empty.AsObject,
  }

  export enum ResponseCase { 
    RESPONSE_NOT_SET = 0,
    CHAT_RESPONSE = 10,
    ACTION_RESPONSE = 11,
    EMPTY = 99,
  }
}

export class ChatResponse extends jspb.Message {
  getMessage(): string;
  setMessage(value: string): ChatResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ChatResponse.AsObject;
  static toObject(includeInstance: boolean, msg: ChatResponse): ChatResponse.AsObject;
  static serializeBinaryToWriter(message: ChatResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ChatResponse;
  static deserializeBinaryFromReader(message: ChatResponse, reader: jspb.BinaryReader): ChatResponse;
}

export namespace ChatResponse {
  export type AsObject = {
    message: string,
  }
}

export class ActionRequiredResponse extends jspb.Message {
  getType(): ActionType;
  setType(value: ActionType): ActionRequiredResponse;

  getActionId(): string;
  setActionId(value: string): ActionRequiredResponse;

  getMessage(): string;
  setMessage(value: string): ActionRequiredResponse;

  getOptionsList(): Array<string>;
  setOptionsList(value: Array<string>): ActionRequiredResponse;
  clearOptionsList(): ActionRequiredResponse;
  addOptions(value: string, index?: number): ActionRequiredResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ActionRequiredResponse.AsObject;
  static toObject(includeInstance: boolean, msg: ActionRequiredResponse): ActionRequiredResponse.AsObject;
  static serializeBinaryToWriter(message: ActionRequiredResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ActionRequiredResponse;
  static deserializeBinaryFromReader(message: ActionRequiredResponse, reader: jspb.BinaryReader): ActionRequiredResponse;
}

export namespace ActionRequiredResponse {
  export type AsObject = {
    type: ActionType,
    actionId: string,
    message: string,
    optionsList: Array<string>,
  }
}

export enum RequestCode { 
  REQUEST_UNKNOWN = 0,
  CHAT = 1,
  FETCH = 2,
  ACTION_RESULT = 3,
}
export enum AppType { 
  APP_UNKNOWN = 0,
  GOOGLE_GMAIL = 1,
  GOOGLE_CALENDAR = 2,
  GITHUB = 3,
  SLACK = 4,
  DISCORD = 5,
  TWITTER = 6,
  WEB_BROWSER = 7,
  TWILIO = 8,
}
export enum ResponseCode { 
  RESPONSE_UNKNOWN = 0,
  SUCCESS = 1,
  FAILED = 2,
  MESSAGE = 3,
  ACTION_REQUIRED = 4,
  FINISHED = 5,
}
export enum ActionType { 
  UNKNOWN_ACTION = 0,
  INFORMATION = 1,
  SINGLE_SELECTION = 2,
  MULTIPLE_SELECTION = 3,
  CONFIRMATION = 4,
}
