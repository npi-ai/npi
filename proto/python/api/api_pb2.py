# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: api/api.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rapi/api.proto\x12\x0cnpi.core.api\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1egoogle/protobuf/wrappers.proto\"r\n\x0b\x43hatRequest\x12\x12\n\nrequest_id\x18\x01 \x01(\t\x12\'\n\x08\x61pp_type\x18\x02 \x01(\x0e\x32\x15.npi.core.api.AppType\x12\x13\n\x0binstruction\x18\x03 \x01(\t\x12\x11\n\tthread_id\x18\x04 \x01(\t\"a\n\x0c\x43hatResponse\x12\x12\n\nrequest_id\x18\x01 \x01(\t\x12,\n\x04type\x18\x02 \x01(\x0e\x32\x1e.npi.core.api.ChatResponseType\x12\x0f\n\x07message\x18\x03 \x01(\t*r\n\x07\x41ppType\x12\x0f\n\x0b\x41PP_UNKNOWN\x10\x00\x12\x10\n\x0cGOOGLE_GMAIL\x10\x01\x12\x13\n\x0fGOOGLE_CALENDAR\x10\x02\x12\n\n\x06GITHUB\x10\x03\x12\t\n\x05SLACK\x10\x04\x12\x0b\n\x07\x44ISCORD\x10\x05\x12\x0b\n\x07TWITTER\x10\x06*p\n\x10\x43hatResponseType\x12\x13\n\x0f\x41PP_UNSUPPORTED\x10\x00\x12\x0b\n\x07SUCCESS\x10\x01\x12\n\n\x06\x46\x41ILED\x10\x02\x12\x0b\n\x07MESSAGE\x10\x03\x12\x12\n\x0eHUMAN_FEEDBACK\x10\x04\x12\r\n\tSAFEGUARD\x10\x05\x32O\n\nChatServer\x12\x41\n\x04\x43hat\x12\x19.npi.core.api.ChatRequest\x1a\x1a.npi.core.api.ChatResponse(\x01\x30\x01\x42\x1eZ\x1cgithub.com/npi-ai/npi/serverb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'api.api_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z\034github.com/npi-ai/npi/server'
  _globals['_APPTYPE']._serialized_start=340
  _globals['_APPTYPE']._serialized_end=454
  _globals['_CHATRESPONSETYPE']._serialized_start=456
  _globals['_CHATRESPONSETYPE']._serialized_end=568
  _globals['_CHATREQUEST']._serialized_start=125
  _globals['_CHATREQUEST']._serialized_end=239
  _globals['_CHATRESPONSE']._serialized_start=241
  _globals['_CHATRESPONSE']._serialized_end=338
  _globals['_CHATSERVER']._serialized_start=570
  _globals['_CHATSERVER']._serialized_end=649
# @@protoc_insertion_point(module_scope)
