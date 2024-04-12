// Code generated by protoc-gen-go. DO NOT EDIT.
// versions:
// 	protoc-gen-go v1.33.0
// 	protoc        v3.19.4
// source: api/api.proto

package server

import (
	protoreflect "google.golang.org/protobuf/reflect/protoreflect"
	protoimpl "google.golang.org/protobuf/runtime/protoimpl"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	_ "google.golang.org/protobuf/types/known/timestamppb"
	_ "google.golang.org/protobuf/types/known/wrapperspb"
	reflect "reflect"
	sync "sync"
)

const (
	// Verify that this generated code is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(20 - protoimpl.MinVersion)
	// Verify that runtime/protoimpl is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(protoimpl.MaxVersion - 20)
)

type RequestCode int32

const (
	RequestCode_REQUEST_UNKNOWN RequestCode = 0
	RequestCode_CHAT            RequestCode = 1
	RequestCode_FETCH           RequestCode = 2
	RequestCode_ACTION_RESULT   RequestCode = 3
)

// Enum value maps for RequestCode.
var (
	RequestCode_name = map[int32]string{
		0: "REQUEST_UNKNOWN",
		1: "CHAT",
		2: "FETCH",
		3: "ACTION_RESULT",
	}
	RequestCode_value = map[string]int32{
		"REQUEST_UNKNOWN": 0,
		"CHAT":            1,
		"FETCH":           2,
		"ACTION_RESULT":   3,
	}
)

func (x RequestCode) Enum() *RequestCode {
	p := new(RequestCode)
	*p = x
	return p
}

func (x RequestCode) String() string {
	return protoimpl.X.EnumStringOf(x.Descriptor(), protoreflect.EnumNumber(x))
}

func (RequestCode) Descriptor() protoreflect.EnumDescriptor {
	return file_api_api_proto_enumTypes[0].Descriptor()
}

func (RequestCode) Type() protoreflect.EnumType {
	return &file_api_api_proto_enumTypes[0]
}

func (x RequestCode) Number() protoreflect.EnumNumber {
	return protoreflect.EnumNumber(x)
}

// Deprecated: Use RequestCode.Descriptor instead.
func (RequestCode) EnumDescriptor() ([]byte, []int) {
	return file_api_api_proto_rawDescGZIP(), []int{0}
}

type ResponseCode int32

const (
	ResponseCode_RESPONSE_UNKNOWN ResponseCode = 0
	ResponseCode_SUCCESS          ResponseCode = 1
	ResponseCode_FAILED           ResponseCode = 2
	ResponseCode_MESSAGE          ResponseCode = 3
	ResponseCode_HUMAN_FEEDBACK   ResponseCode = 4
	// SAFEGUARD = 5;
	ResponseCode_CLIENT_ACTION ResponseCode = 6
)

// Enum value maps for ResponseCode.
var (
	ResponseCode_name = map[int32]string{
		0: "RESPONSE_UNKNOWN",
		1: "SUCCESS",
		2: "FAILED",
		3: "MESSAGE",
		4: "HUMAN_FEEDBACK",
		6: "CLIENT_ACTION",
	}
	ResponseCode_value = map[string]int32{
		"RESPONSE_UNKNOWN": 0,
		"SUCCESS":          1,
		"FAILED":           2,
		"MESSAGE":          3,
		"HUMAN_FEEDBACK":   4,
		"CLIENT_ACTION":    6,
	}
)

func (x ResponseCode) Enum() *ResponseCode {
	p := new(ResponseCode)
	*p = x
	return p
}

func (x ResponseCode) String() string {
	return protoimpl.X.EnumStringOf(x.Descriptor(), protoreflect.EnumNumber(x))
}

func (ResponseCode) Descriptor() protoreflect.EnumDescriptor {
	return file_api_api_proto_enumTypes[1].Descriptor()
}

func (ResponseCode) Type() protoreflect.EnumType {
	return &file_api_api_proto_enumTypes[1]
}

func (x ResponseCode) Number() protoreflect.EnumNumber {
	return protoreflect.EnumNumber(x)
}

// Deprecated: Use ResponseCode.Descriptor instead.
func (ResponseCode) EnumDescriptor() ([]byte, []int) {
	return file_api_api_proto_rawDescGZIP(), []int{1}
}

type AppType int32

const (
	AppType_APP_UNKNOWN     AppType = 0
	AppType_GOOGLE_GMAIL    AppType = 1
	AppType_GOOGLE_CALENDAR AppType = 2
	AppType_GITHUB          AppType = 3
	AppType_SLACK           AppType = 4
	AppType_DISCORD         AppType = 5
	AppType_TWITTER         AppType = 6
)

// Enum value maps for AppType.
var (
	AppType_name = map[int32]string{
		0: "APP_UNKNOWN",
		1: "GOOGLE_GMAIL",
		2: "GOOGLE_CALENDAR",
		3: "GITHUB",
		4: "SLACK",
		5: "DISCORD",
		6: "TWITTER",
	}
	AppType_value = map[string]int32{
		"APP_UNKNOWN":     0,
		"GOOGLE_GMAIL":    1,
		"GOOGLE_CALENDAR": 2,
		"GITHUB":          3,
		"SLACK":           4,
		"DISCORD":         5,
		"TWITTER":         6,
	}
)

func (x AppType) Enum() *AppType {
	p := new(AppType)
	*p = x
	return p
}

func (x AppType) String() string {
	return protoimpl.X.EnumStringOf(x.Descriptor(), protoreflect.EnumNumber(x))
}

func (AppType) Descriptor() protoreflect.EnumDescriptor {
	return file_api_api_proto_enumTypes[2].Descriptor()
}

func (AppType) Type() protoreflect.EnumType {
	return &file_api_api_proto_enumTypes[2]
}

func (x AppType) Number() protoreflect.EnumNumber {
	return protoreflect.EnumNumber(x)
}

// Deprecated: Use AppType.Descriptor instead.
func (AppType) EnumDescriptor() ([]byte, []int) {
	return file_api_api_proto_rawDescGZIP(), []int{2}
}

type Request struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Code      RequestCode `protobuf:"varint,1,opt,name=code,proto3,enum=npi.core.api.RequestCode" json:"code,omitempty"`
	RequestId string      `protobuf:"bytes,2,opt,name=request_id,json=requestId,proto3" json:"request_id,omitempty"`
	ThreadId  string      `protobuf:"bytes,3,opt,name=thread_id,json=threadId,proto3" json:"thread_id,omitempty"`
	// Types that are assignable to Request:
	//
	//	*Request_ChatRequest
	//	*Request_ActionResultRequest
	//	*Request_Empty
	Request isRequest_Request `protobuf_oneof:"request"`
}

func (x *Request) Reset() {
	*x = Request{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_api_proto_msgTypes[0]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *Request) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*Request) ProtoMessage() {}

func (x *Request) ProtoReflect() protoreflect.Message {
	mi := &file_api_api_proto_msgTypes[0]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use Request.ProtoReflect.Descriptor instead.
func (*Request) Descriptor() ([]byte, []int) {
	return file_api_api_proto_rawDescGZIP(), []int{0}
}

func (x *Request) GetCode() RequestCode {
	if x != nil {
		return x.Code
	}
	return RequestCode_REQUEST_UNKNOWN
}

func (x *Request) GetRequestId() string {
	if x != nil {
		return x.RequestId
	}
	return ""
}

func (x *Request) GetThreadId() string {
	if x != nil {
		return x.ThreadId
	}
	return ""
}

func (m *Request) GetRequest() isRequest_Request {
	if m != nil {
		return m.Request
	}
	return nil
}

func (x *Request) GetChatRequest() *ChatRequest {
	if x, ok := x.GetRequest().(*Request_ChatRequest); ok {
		return x.ChatRequest
	}
	return nil
}

func (x *Request) GetActionResultRequest() *ActionResultRequest {
	if x, ok := x.GetRequest().(*Request_ActionResultRequest); ok {
		return x.ActionResultRequest
	}
	return nil
}

func (x *Request) GetEmpty() *emptypb.Empty {
	if x, ok := x.GetRequest().(*Request_Empty); ok {
		return x.Empty
	}
	return nil
}

type isRequest_Request interface {
	isRequest_Request()
}

type Request_ChatRequest struct {
	ChatRequest *ChatRequest `protobuf:"bytes,10,opt,name=chat_request,json=chatRequest,proto3,oneof"`
}

type Request_ActionResultRequest struct {
	ActionResultRequest *ActionResultRequest `protobuf:"bytes,12,opt,name=action_result_request,json=actionResultRequest,proto3,oneof"`
}

type Request_Empty struct {
	Empty *emptypb.Empty `protobuf:"bytes,99,opt,name=empty,proto3,oneof"`
}

func (*Request_ChatRequest) isRequest_Request() {}

func (*Request_ActionResultRequest) isRequest_Request() {}

func (*Request_Empty) isRequest_Request() {}

type Response struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Code      ResponseCode `protobuf:"varint,1,opt,name=code,proto3,enum=npi.core.api.ResponseCode" json:"code,omitempty"`
	RequestId string       `protobuf:"bytes,2,opt,name=request_id,json=requestId,proto3" json:"request_id,omitempty"`
	ThreadId  string       `protobuf:"bytes,3,opt,name=thread_id,json=threadId,proto3" json:"thread_id,omitempty"`
	// Types that are assignable to Response:
	//
	//	*Response_ChatResponse
	//	*Response_Empty
	Response isResponse_Response `protobuf_oneof:"response"`
}

func (x *Response) Reset() {
	*x = Response{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_api_proto_msgTypes[1]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *Response) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*Response) ProtoMessage() {}

func (x *Response) ProtoReflect() protoreflect.Message {
	mi := &file_api_api_proto_msgTypes[1]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use Response.ProtoReflect.Descriptor instead.
func (*Response) Descriptor() ([]byte, []int) {
	return file_api_api_proto_rawDescGZIP(), []int{1}
}

func (x *Response) GetCode() ResponseCode {
	if x != nil {
		return x.Code
	}
	return ResponseCode_RESPONSE_UNKNOWN
}

func (x *Response) GetRequestId() string {
	if x != nil {
		return x.RequestId
	}
	return ""
}

func (x *Response) GetThreadId() string {
	if x != nil {
		return x.ThreadId
	}
	return ""
}

func (m *Response) GetResponse() isResponse_Response {
	if m != nil {
		return m.Response
	}
	return nil
}

func (x *Response) GetChatResponse() *ChatResponse {
	if x, ok := x.GetResponse().(*Response_ChatResponse); ok {
		return x.ChatResponse
	}
	return nil
}

func (x *Response) GetEmpty() *emptypb.Empty {
	if x, ok := x.GetResponse().(*Response_Empty); ok {
		return x.Empty
	}
	return nil
}

type isResponse_Response interface {
	isResponse_Response()
}

type Response_ChatResponse struct {
	ChatResponse *ChatResponse `protobuf:"bytes,10,opt,name=chat_response,json=chatResponse,proto3,oneof"`
}

type Response_Empty struct {
	Empty *emptypb.Empty `protobuf:"bytes,99,opt,name=empty,proto3,oneof"`
}

func (*Response_ChatResponse) isResponse_Response() {}

func (*Response_Empty) isResponse_Response() {}

type ChatRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	AppType     AppType `protobuf:"varint,1,opt,name=app_type,json=appType,proto3,enum=npi.core.api.AppType" json:"app_type,omitempty"`
	Instruction string  `protobuf:"bytes,2,opt,name=instruction,proto3" json:"instruction,omitempty"`
}

func (x *ChatRequest) Reset() {
	*x = ChatRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_api_proto_msgTypes[2]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *ChatRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*ChatRequest) ProtoMessage() {}

func (x *ChatRequest) ProtoReflect() protoreflect.Message {
	mi := &file_api_api_proto_msgTypes[2]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use ChatRequest.ProtoReflect.Descriptor instead.
func (*ChatRequest) Descriptor() ([]byte, []int) {
	return file_api_api_proto_rawDescGZIP(), []int{2}
}

func (x *ChatRequest) GetAppType() AppType {
	if x != nil {
		return x.AppType
	}
	return AppType_APP_UNKNOWN
}

func (x *ChatRequest) GetInstruction() string {
	if x != nil {
		return x.Instruction
	}
	return ""
}

type ChatResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	ThreadId string `protobuf:"bytes,1,opt,name=thread_id,json=threadId,proto3" json:"thread_id,omitempty"`
	Message  string `protobuf:"bytes,2,opt,name=message,proto3" json:"message,omitempty"`
}

func (x *ChatResponse) Reset() {
	*x = ChatResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_api_proto_msgTypes[3]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *ChatResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*ChatResponse) ProtoMessage() {}

func (x *ChatResponse) ProtoReflect() protoreflect.Message {
	mi := &file_api_api_proto_msgTypes[3]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use ChatResponse.ProtoReflect.Descriptor instead.
func (*ChatResponse) Descriptor() ([]byte, []int) {
	return file_api_api_proto_rawDescGZIP(), []int{3}
}

func (x *ChatResponse) GetThreadId() string {
	if x != nil {
		return x.ThreadId
	}
	return ""
}

func (x *ChatResponse) GetMessage() string {
	if x != nil {
		return x.Message
	}
	return ""
}

type ActionResultRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	ActionId     string `protobuf:"bytes,1,opt,name=action_id,json=actionId,proto3" json:"action_id,omitempty"`
	ActionResult string `protobuf:"bytes,2,opt,name=action_result,json=actionResult,proto3" json:"action_result,omitempty"`
}

func (x *ActionResultRequest) Reset() {
	*x = ActionResultRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_api_proto_msgTypes[4]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *ActionResultRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*ActionResultRequest) ProtoMessage() {}

func (x *ActionResultRequest) ProtoReflect() protoreflect.Message {
	mi := &file_api_api_proto_msgTypes[4]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use ActionResultRequest.ProtoReflect.Descriptor instead.
func (*ActionResultRequest) Descriptor() ([]byte, []int) {
	return file_api_api_proto_rawDescGZIP(), []int{4}
}

func (x *ActionResultRequest) GetActionId() string {
	if x != nil {
		return x.ActionId
	}
	return ""
}

func (x *ActionResultRequest) GetActionResult() string {
	if x != nil {
		return x.ActionResult
	}
	return ""
}

var File_api_api_proto protoreflect.FileDescriptor

var file_api_api_proto_rawDesc = []byte{
	0x0a, 0x0d, 0x61, 0x70, 0x69, 0x2f, 0x61, 0x70, 0x69, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x12,
	0x0c, 0x6e, 0x70, 0x69, 0x2e, 0x63, 0x6f, 0x72, 0x65, 0x2e, 0x61, 0x70, 0x69, 0x1a, 0x1b, 0x67,
	0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2f, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2f, 0x65,
	0x6d, 0x70, 0x74, 0x79, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x1a, 0x1f, 0x67, 0x6f, 0x6f, 0x67,
	0x6c, 0x65, 0x2f, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2f, 0x74, 0x69, 0x6d, 0x65,
	0x73, 0x74, 0x61, 0x6d, 0x70, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x1a, 0x1e, 0x67, 0x6f, 0x6f,
	0x67, 0x6c, 0x65, 0x2f, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2f, 0x77, 0x72, 0x61,
	0x70, 0x70, 0x65, 0x72, 0x73, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x22, 0xc8, 0x02, 0x0a, 0x07,
	0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x2d, 0x0a, 0x04, 0x63, 0x6f, 0x64, 0x65, 0x18,
	0x01, 0x20, 0x01, 0x28, 0x0e, 0x32, 0x19, 0x2e, 0x6e, 0x70, 0x69, 0x2e, 0x63, 0x6f, 0x72, 0x65,
	0x2e, 0x61, 0x70, 0x69, 0x2e, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x43, 0x6f, 0x64, 0x65,
	0x52, 0x04, 0x63, 0x6f, 0x64, 0x65, 0x12, 0x1d, 0x0a, 0x0a, 0x72, 0x65, 0x71, 0x75, 0x65, 0x73,
	0x74, 0x5f, 0x69, 0x64, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x09, 0x72, 0x65, 0x71, 0x75,
	0x65, 0x73, 0x74, 0x49, 0x64, 0x12, 0x1b, 0x0a, 0x09, 0x74, 0x68, 0x72, 0x65, 0x61, 0x64, 0x5f,
	0x69, 0x64, 0x18, 0x03, 0x20, 0x01, 0x28, 0x09, 0x52, 0x08, 0x74, 0x68, 0x72, 0x65, 0x61, 0x64,
	0x49, 0x64, 0x12, 0x3e, 0x0a, 0x0c, 0x63, 0x68, 0x61, 0x74, 0x5f, 0x72, 0x65, 0x71, 0x75, 0x65,
	0x73, 0x74, 0x18, 0x0a, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x19, 0x2e, 0x6e, 0x70, 0x69, 0x2e, 0x63,
	0x6f, 0x72, 0x65, 0x2e, 0x61, 0x70, 0x69, 0x2e, 0x43, 0x68, 0x61, 0x74, 0x52, 0x65, 0x71, 0x75,
	0x65, 0x73, 0x74, 0x48, 0x00, 0x52, 0x0b, 0x63, 0x68, 0x61, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65,
	0x73, 0x74, 0x12, 0x57, 0x0a, 0x15, 0x61, 0x63, 0x74, 0x69, 0x6f, 0x6e, 0x5f, 0x72, 0x65, 0x73,
	0x75, 0x6c, 0x74, 0x5f, 0x72, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x18, 0x0c, 0x20, 0x01, 0x28,
	0x0b, 0x32, 0x21, 0x2e, 0x6e, 0x70, 0x69, 0x2e, 0x63, 0x6f, 0x72, 0x65, 0x2e, 0x61, 0x70, 0x69,
	0x2e, 0x41, 0x63, 0x74, 0x69, 0x6f, 0x6e, 0x52, 0x65, 0x73, 0x75, 0x6c, 0x74, 0x52, 0x65, 0x71,
	0x75, 0x65, 0x73, 0x74, 0x48, 0x00, 0x52, 0x13, 0x61, 0x63, 0x74, 0x69, 0x6f, 0x6e, 0x52, 0x65,
	0x73, 0x75, 0x6c, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x2e, 0x0a, 0x05, 0x65,
	0x6d, 0x70, 0x74, 0x79, 0x18, 0x63, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x16, 0x2e, 0x67, 0x6f, 0x6f,
	0x67, 0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2e, 0x45, 0x6d, 0x70,
	0x74, 0x79, 0x48, 0x00, 0x52, 0x05, 0x65, 0x6d, 0x70, 0x74, 0x79, 0x42, 0x09, 0x0a, 0x07, 0x72,
	0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x22, 0xf5, 0x01, 0x0a, 0x08, 0x52, 0x65, 0x73, 0x70, 0x6f,
	0x6e, 0x73, 0x65, 0x12, 0x2e, 0x0a, 0x04, 0x63, 0x6f, 0x64, 0x65, 0x18, 0x01, 0x20, 0x01, 0x28,
	0x0e, 0x32, 0x1a, 0x2e, 0x6e, 0x70, 0x69, 0x2e, 0x63, 0x6f, 0x72, 0x65, 0x2e, 0x61, 0x70, 0x69,
	0x2e, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x43, 0x6f, 0x64, 0x65, 0x52, 0x04, 0x63,
	0x6f, 0x64, 0x65, 0x12, 0x1d, 0x0a, 0x0a, 0x72, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x5f, 0x69,
	0x64, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x09, 0x72, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74,
	0x49, 0x64, 0x12, 0x1b, 0x0a, 0x09, 0x74, 0x68, 0x72, 0x65, 0x61, 0x64, 0x5f, 0x69, 0x64, 0x18,
	0x03, 0x20, 0x01, 0x28, 0x09, 0x52, 0x08, 0x74, 0x68, 0x72, 0x65, 0x61, 0x64, 0x49, 0x64, 0x12,
	0x41, 0x0a, 0x0d, 0x63, 0x68, 0x61, 0x74, 0x5f, 0x72, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65,
	0x18, 0x0a, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x1a, 0x2e, 0x6e, 0x70, 0x69, 0x2e, 0x63, 0x6f, 0x72,
	0x65, 0x2e, 0x61, 0x70, 0x69, 0x2e, 0x43, 0x68, 0x61, 0x74, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e,
	0x73, 0x65, 0x48, 0x00, 0x52, 0x0c, 0x63, 0x68, 0x61, 0x74, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e,
	0x73, 0x65, 0x12, 0x2e, 0x0a, 0x05, 0x65, 0x6d, 0x70, 0x74, 0x79, 0x18, 0x63, 0x20, 0x01, 0x28,
	0x0b, 0x32, 0x16, 0x2e, 0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f,
	0x62, 0x75, 0x66, 0x2e, 0x45, 0x6d, 0x70, 0x74, 0x79, 0x48, 0x00, 0x52, 0x05, 0x65, 0x6d, 0x70,
	0x74, 0x79, 0x42, 0x0a, 0x0a, 0x08, 0x72, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x22, 0x61,
	0x0a, 0x0b, 0x43, 0x68, 0x61, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x30, 0x0a,
	0x08, 0x61, 0x70, 0x70, 0x5f, 0x74, 0x79, 0x70, 0x65, 0x18, 0x01, 0x20, 0x01, 0x28, 0x0e, 0x32,
	0x15, 0x2e, 0x6e, 0x70, 0x69, 0x2e, 0x63, 0x6f, 0x72, 0x65, 0x2e, 0x61, 0x70, 0x69, 0x2e, 0x41,
	0x70, 0x70, 0x54, 0x79, 0x70, 0x65, 0x52, 0x07, 0x61, 0x70, 0x70, 0x54, 0x79, 0x70, 0x65, 0x12,
	0x20, 0x0a, 0x0b, 0x69, 0x6e, 0x73, 0x74, 0x72, 0x75, 0x63, 0x74, 0x69, 0x6f, 0x6e, 0x18, 0x02,
	0x20, 0x01, 0x28, 0x09, 0x52, 0x0b, 0x69, 0x6e, 0x73, 0x74, 0x72, 0x75, 0x63, 0x74, 0x69, 0x6f,
	0x6e, 0x22, 0x45, 0x0a, 0x0c, 0x43, 0x68, 0x61, 0x74, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73,
	0x65, 0x12, 0x1b, 0x0a, 0x09, 0x74, 0x68, 0x72, 0x65, 0x61, 0x64, 0x5f, 0x69, 0x64, 0x18, 0x01,
	0x20, 0x01, 0x28, 0x09, 0x52, 0x08, 0x74, 0x68, 0x72, 0x65, 0x61, 0x64, 0x49, 0x64, 0x12, 0x18,
	0x0a, 0x07, 0x6d, 0x65, 0x73, 0x73, 0x61, 0x67, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52,
	0x07, 0x6d, 0x65, 0x73, 0x73, 0x61, 0x67, 0x65, 0x22, 0x57, 0x0a, 0x13, 0x41, 0x63, 0x74, 0x69,
	0x6f, 0x6e, 0x52, 0x65, 0x73, 0x75, 0x6c, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12,
	0x1b, 0x0a, 0x09, 0x61, 0x63, 0x74, 0x69, 0x6f, 0x6e, 0x5f, 0x69, 0x64, 0x18, 0x01, 0x20, 0x01,
	0x28, 0x09, 0x52, 0x08, 0x61, 0x63, 0x74, 0x69, 0x6f, 0x6e, 0x49, 0x64, 0x12, 0x23, 0x0a, 0x0d,
	0x61, 0x63, 0x74, 0x69, 0x6f, 0x6e, 0x5f, 0x72, 0x65, 0x73, 0x75, 0x6c, 0x74, 0x18, 0x02, 0x20,
	0x01, 0x28, 0x09, 0x52, 0x0c, 0x61, 0x63, 0x74, 0x69, 0x6f, 0x6e, 0x52, 0x65, 0x73, 0x75, 0x6c,
	0x74, 0x2a, 0x4a, 0x0a, 0x0b, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x43, 0x6f, 0x64, 0x65,
	0x12, 0x13, 0x0a, 0x0f, 0x52, 0x45, 0x51, 0x55, 0x45, 0x53, 0x54, 0x5f, 0x55, 0x4e, 0x4b, 0x4e,
	0x4f, 0x57, 0x4e, 0x10, 0x00, 0x12, 0x08, 0x0a, 0x04, 0x43, 0x48, 0x41, 0x54, 0x10, 0x01, 0x12,
	0x09, 0x0a, 0x05, 0x46, 0x45, 0x54, 0x43, 0x48, 0x10, 0x02, 0x12, 0x11, 0x0a, 0x0d, 0x41, 0x43,
	0x54, 0x49, 0x4f, 0x4e, 0x5f, 0x52, 0x45, 0x53, 0x55, 0x4c, 0x54, 0x10, 0x03, 0x2a, 0x71, 0x0a,
	0x0c, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x43, 0x6f, 0x64, 0x65, 0x12, 0x14, 0x0a,
	0x10, 0x52, 0x45, 0x53, 0x50, 0x4f, 0x4e, 0x53, 0x45, 0x5f, 0x55, 0x4e, 0x4b, 0x4e, 0x4f, 0x57,
	0x4e, 0x10, 0x00, 0x12, 0x0b, 0x0a, 0x07, 0x53, 0x55, 0x43, 0x43, 0x45, 0x53, 0x53, 0x10, 0x01,
	0x12, 0x0a, 0x0a, 0x06, 0x46, 0x41, 0x49, 0x4c, 0x45, 0x44, 0x10, 0x02, 0x12, 0x0b, 0x0a, 0x07,
	0x4d, 0x45, 0x53, 0x53, 0x41, 0x47, 0x45, 0x10, 0x03, 0x12, 0x12, 0x0a, 0x0e, 0x48, 0x55, 0x4d,
	0x41, 0x4e, 0x5f, 0x46, 0x45, 0x45, 0x44, 0x42, 0x41, 0x43, 0x4b, 0x10, 0x04, 0x12, 0x11, 0x0a,
	0x0d, 0x43, 0x4c, 0x49, 0x45, 0x4e, 0x54, 0x5f, 0x41, 0x43, 0x54, 0x49, 0x4f, 0x4e, 0x10, 0x06,
	0x2a, 0x72, 0x0a, 0x07, 0x41, 0x70, 0x70, 0x54, 0x79, 0x70, 0x65, 0x12, 0x0f, 0x0a, 0x0b, 0x41,
	0x50, 0x50, 0x5f, 0x55, 0x4e, 0x4b, 0x4e, 0x4f, 0x57, 0x4e, 0x10, 0x00, 0x12, 0x10, 0x0a, 0x0c,
	0x47, 0x4f, 0x4f, 0x47, 0x4c, 0x45, 0x5f, 0x47, 0x4d, 0x41, 0x49, 0x4c, 0x10, 0x01, 0x12, 0x13,
	0x0a, 0x0f, 0x47, 0x4f, 0x4f, 0x47, 0x4c, 0x45, 0x5f, 0x43, 0x41, 0x4c, 0x45, 0x4e, 0x44, 0x41,
	0x52, 0x10, 0x02, 0x12, 0x0a, 0x0a, 0x06, 0x47, 0x49, 0x54, 0x48, 0x55, 0x42, 0x10, 0x03, 0x12,
	0x09, 0x0a, 0x05, 0x53, 0x4c, 0x41, 0x43, 0x4b, 0x10, 0x04, 0x12, 0x0b, 0x0a, 0x07, 0x44, 0x49,
	0x53, 0x43, 0x4f, 0x52, 0x44, 0x10, 0x05, 0x12, 0x0b, 0x0a, 0x07, 0x54, 0x57, 0x49, 0x54, 0x54,
	0x45, 0x52, 0x10, 0x06, 0x32, 0x43, 0x0a, 0x0a, 0x43, 0x68, 0x61, 0x74, 0x53, 0x65, 0x72, 0x76,
	0x65, 0x72, 0x12, 0x35, 0x0a, 0x04, 0x43, 0x68, 0x61, 0x74, 0x12, 0x15, 0x2e, 0x6e, 0x70, 0x69,
	0x2e, 0x63, 0x6f, 0x72, 0x65, 0x2e, 0x61, 0x70, 0x69, 0x2e, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73,
	0x74, 0x1a, 0x16, 0x2e, 0x6e, 0x70, 0x69, 0x2e, 0x63, 0x6f, 0x72, 0x65, 0x2e, 0x61, 0x70, 0x69,
	0x2e, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x42, 0x1e, 0x5a, 0x1c, 0x67, 0x69, 0x74,
	0x68, 0x75, 0x62, 0x2e, 0x63, 0x6f, 0x6d, 0x2f, 0x6e, 0x70, 0x69, 0x2d, 0x61, 0x69, 0x2f, 0x6e,
	0x70, 0x69, 0x2f, 0x73, 0x65, 0x72, 0x76, 0x65, 0x72, 0x62, 0x06, 0x70, 0x72, 0x6f, 0x74, 0x6f,
	0x33,
}

var (
	file_api_api_proto_rawDescOnce sync.Once
	file_api_api_proto_rawDescData = file_api_api_proto_rawDesc
)

func file_api_api_proto_rawDescGZIP() []byte {
	file_api_api_proto_rawDescOnce.Do(func() {
		file_api_api_proto_rawDescData = protoimpl.X.CompressGZIP(file_api_api_proto_rawDescData)
	})
	return file_api_api_proto_rawDescData
}

var file_api_api_proto_enumTypes = make([]protoimpl.EnumInfo, 3)
var file_api_api_proto_msgTypes = make([]protoimpl.MessageInfo, 5)
var file_api_api_proto_goTypes = []interface{}{
	(RequestCode)(0),            // 0: npi.core.api.RequestCode
	(ResponseCode)(0),           // 1: npi.core.api.ResponseCode
	(AppType)(0),                // 2: npi.core.api.AppType
	(*Request)(nil),             // 3: npi.core.api.Request
	(*Response)(nil),            // 4: npi.core.api.Response
	(*ChatRequest)(nil),         // 5: npi.core.api.ChatRequest
	(*ChatResponse)(nil),        // 6: npi.core.api.ChatResponse
	(*ActionResultRequest)(nil), // 7: npi.core.api.ActionResultRequest
	(*emptypb.Empty)(nil),       // 8: google.protobuf.Empty
}
var file_api_api_proto_depIdxs = []int32{
	0, // 0: npi.core.api.Request.code:type_name -> npi.core.api.RequestCode
	5, // 1: npi.core.api.Request.chat_request:type_name -> npi.core.api.ChatRequest
	7, // 2: npi.core.api.Request.action_result_request:type_name -> npi.core.api.ActionResultRequest
	8, // 3: npi.core.api.Request.empty:type_name -> google.protobuf.Empty
	1, // 4: npi.core.api.Response.code:type_name -> npi.core.api.ResponseCode
	6, // 5: npi.core.api.Response.chat_response:type_name -> npi.core.api.ChatResponse
	8, // 6: npi.core.api.Response.empty:type_name -> google.protobuf.Empty
	2, // 7: npi.core.api.ChatRequest.app_type:type_name -> npi.core.api.AppType
	3, // 8: npi.core.api.ChatServer.Chat:input_type -> npi.core.api.Request
	4, // 9: npi.core.api.ChatServer.Chat:output_type -> npi.core.api.Response
	9, // [9:10] is the sub-list for method output_type
	8, // [8:9] is the sub-list for method input_type
	8, // [8:8] is the sub-list for extension type_name
	8, // [8:8] is the sub-list for extension extendee
	0, // [0:8] is the sub-list for field type_name
}

func init() { file_api_api_proto_init() }
func file_api_api_proto_init() {
	if File_api_api_proto != nil {
		return
	}
	if !protoimpl.UnsafeEnabled {
		file_api_api_proto_msgTypes[0].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*Request); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_api_proto_msgTypes[1].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*Response); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_api_proto_msgTypes[2].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*ChatRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_api_proto_msgTypes[3].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*ChatResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_api_proto_msgTypes[4].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*ActionResultRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
	}
	file_api_api_proto_msgTypes[0].OneofWrappers = []interface{}{
		(*Request_ChatRequest)(nil),
		(*Request_ActionResultRequest)(nil),
		(*Request_Empty)(nil),
	}
	file_api_api_proto_msgTypes[1].OneofWrappers = []interface{}{
		(*Response_ChatResponse)(nil),
		(*Response_Empty)(nil),
	}
	type x struct{}
	out := protoimpl.TypeBuilder{
		File: protoimpl.DescBuilder{
			GoPackagePath: reflect.TypeOf(x{}).PkgPath(),
			RawDescriptor: file_api_api_proto_rawDesc,
			NumEnums:      3,
			NumMessages:   5,
			NumExtensions: 0,
			NumServices:   1,
		},
		GoTypes:           file_api_api_proto_goTypes,
		DependencyIndexes: file_api_api_proto_depIdxs,
		EnumInfos:         file_api_api_proto_enumTypes,
		MessageInfos:      file_api_api_proto_msgTypes,
	}.Build()
	File_api_api_proto = out.File
	file_api_api_proto_rawDesc = nil
	file_api_api_proto_goTypes = nil
	file_api_api_proto_depIdxs = nil
}
