// Code generated by protoc-gen-go-grpc. DO NOT EDIT.
// versions:
// - protoc-gen-go-grpc v1.3.0
// - protoc             v3.19.4
// source: controller.proto

package server

import (
	context "context"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
// Requires gRPC-Go v1.32.0 or later.
const _ = grpc.SupportPackageIsVersion7

const (
	Controller_RegisterTool_FullMethodName   = "/npi.core.controller.Controller/RegisterTool"
	Controller_UnregisterTool_FullMethodName = "/npi.core.controller.Controller/UnregisterTool"
	Controller_Heartbeat_FullMethodName      = "/npi.core.controller.Controller/Heartbeat"
)

// ControllerClient is the client API for Controller service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type ControllerClient interface {
	RegisterTool(ctx context.Context, in *RegisterToolRequest, opts ...grpc.CallOption) (*RegisterToolResponse, error)
	UnregisterTool(ctx context.Context, in *emptypb.Empty, opts ...grpc.CallOption) (*emptypb.Empty, error)
	Heartbeat(ctx context.Context, in *emptypb.Empty, opts ...grpc.CallOption) (*emptypb.Empty, error)
}

type controllerClient struct {
	cc grpc.ClientConnInterface
}

func NewControllerClient(cc grpc.ClientConnInterface) ControllerClient {
	return &controllerClient{cc}
}

func (c *controllerClient) RegisterTool(ctx context.Context, in *RegisterToolRequest, opts ...grpc.CallOption) (*RegisterToolResponse, error) {
	out := new(RegisterToolResponse)
	err := c.cc.Invoke(ctx, Controller_RegisterTool_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *controllerClient) UnregisterTool(ctx context.Context, in *emptypb.Empty, opts ...grpc.CallOption) (*emptypb.Empty, error) {
	out := new(emptypb.Empty)
	err := c.cc.Invoke(ctx, Controller_UnregisterTool_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *controllerClient) Heartbeat(ctx context.Context, in *emptypb.Empty, opts ...grpc.CallOption) (*emptypb.Empty, error) {
	out := new(emptypb.Empty)
	err := c.cc.Invoke(ctx, Controller_Heartbeat_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// ControllerServer is the server API for Controller service.
// All implementations should embed UnimplementedControllerServer
// for forward compatibility
type ControllerServer interface {
	RegisterTool(context.Context, *RegisterToolRequest) (*RegisterToolResponse, error)
	UnregisterTool(context.Context, *emptypb.Empty) (*emptypb.Empty, error)
	Heartbeat(context.Context, *emptypb.Empty) (*emptypb.Empty, error)
}

// UnimplementedControllerServer should be embedded to have forward compatible implementations.
type UnimplementedControllerServer struct {
}

func (UnimplementedControllerServer) RegisterTool(context.Context, *RegisterToolRequest) (*RegisterToolResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method RegisterTool not implemented")
}
func (UnimplementedControllerServer) UnregisterTool(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method UnregisterTool not implemented")
}
func (UnimplementedControllerServer) Heartbeat(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Heartbeat not implemented")
}

// UnsafeControllerServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to ControllerServer will
// result in compilation errors.
type UnsafeControllerServer interface {
	mustEmbedUnimplementedControllerServer()
}

func RegisterControllerServer(s grpc.ServiceRegistrar, srv ControllerServer) {
	s.RegisterService(&Controller_ServiceDesc, srv)
}

func _Controller_RegisterTool_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(RegisterToolRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(ControllerServer).RegisterTool(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: Controller_RegisterTool_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(ControllerServer).RegisterTool(ctx, req.(*RegisterToolRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Controller_UnregisterTool_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(emptypb.Empty)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(ControllerServer).UnregisterTool(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: Controller_UnregisterTool_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(ControllerServer).UnregisterTool(ctx, req.(*emptypb.Empty))
	}
	return interceptor(ctx, in, info, handler)
}

func _Controller_Heartbeat_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(emptypb.Empty)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(ControllerServer).Heartbeat(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: Controller_Heartbeat_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(ControllerServer).Heartbeat(ctx, req.(*emptypb.Empty))
	}
	return interceptor(ctx, in, info, handler)
}

// Controller_ServiceDesc is the grpc.ServiceDesc for Controller service.
// It's only intended for direct use with grpc.RegisterService,
// and not to be introspected or modified (even as a copy)
var Controller_ServiceDesc = grpc.ServiceDesc{
	ServiceName: "npi.core.controller.Controller",
	HandlerType: (*ControllerServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "RegisterTool",
			Handler:    _Controller_RegisterTool_Handler,
		},
		{
			MethodName: "UnregisterTool",
			Handler:    _Controller_UnregisterTool_Handler,
		},
		{
			MethodName: "Heartbeat",
			Handler:    _Controller_Heartbeat_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "controller.proto",
}
