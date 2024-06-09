# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: controller.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10\x63ontroller.proto\x12\x13npi.core.controller\x1a\x1bgoogle/protobuf/empty.proto\"n\n\x13RegisterToolRequest\x12+\n\x04tool\x18\x01 \x01(\x0b\x32\x1d.npi.core.controller.ToolSpec\x12\x10\n\x08hostname\x18\x02 \x01(\t\x12\n\n\x02ip\x18\x03 \x01(\t\x12\x0c\n\x04port\x18\x04 \x01(\x05\"%\n\x14RegisterToolResponse\x12\r\n\x05token\x18\x01 \x01(\t\"#\n\x15UnregisterToolRequest\x12\n\n\x02id\x18\x01 \x01(\t\"\x1e\n\x10HeartbeatRequest\x12\n\n\x02id\x18\x01 \x01(\t\"u\n\x08ToolSpec\x12/\n\x08metadata\x18\x01 \x01(\x0b\x32\x1d.npi.core.controller.Metadata\x12\x38\n\rfunction_spec\x18\x02 \x01(\x0b\x32!.npi.core.controller.FunctionSpec\"n\n\x08Metadata\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0f\n\x07version\x18\x03 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x04 \x01(\t\x12\x0e\n\x06\x61uthor\x18\x05 \x01(\t\x12\x12\n\nagent_mode\x18\x06 \x01(\x08\"\xa6\x01\n\x0c\x46unctionSpec\x12-\n\x07runtime\x18\x01 \x01(\x0b\x32\x1c.npi.core.controller.Runtime\x12\x35\n\x0c\x64\x65pendencies\x18\x02 \x03(\x0b\x32\x1f.npi.core.controller.Dependency\x12\x30\n\tfunctions\x18\x03 \x03(\x0b\x32\x1d.npi.core.controller.Function\"Z\n\x07Runtime\x12/\n\x08language\x18\x01 \x01(\x0e\x32\x1d.npi.core.controller.Language\x12\x0f\n\x07version\x18\x02 \x01(\t\x12\r\n\x05image\x18\x03 \x01(\t\"+\n\nDependency\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07version\x18\x02 \x01(\t\"\x92\x01\n\x08\x46unction\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x32\n\nparameters\x18\x03 \x03(\x0b\x32\x1e.npi.core.controller.Parameter\x12/\n\tfew_shots\x18\x04 \x03(\x0b\x32\x1c.npi.core.controller.FewShot\"_\n\tParameter\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x0c\n\x04type\x18\x03 \x01(\t\x12\x0f\n\x07\x64\x65\x66\x61ult\x18\x04 \x01(\t\x12\x10\n\x08required\x18\x05 \x01(\x08\"(\n\x07\x46\x65wShot\x12\r\n\x05input\x18\x01 \x01(\t\x12\x0e\n\x06output\x18\x02 \x01(\t*8\n\x08Language\x12\x14\n\x10UNKNOWN_LANGUAGE\x10\x00\x12\n\n\x06PYTHON\x10\x01\x12\n\n\x06NODEJS\x10\x02*\xa2\x01\n\rParameterType\x12\x10\n\x0cUNKNOWN_TYPE\x10\x00\x12\n\n\x06STRING\x10\x01\x12\x07\n\x03INT\x10\x02\x12\t\n\x05\x46LOAT\x10\x03\x12\x08\n\x04\x42OOL\x10\x04\x12\x07\n\x03MAP\x10\x05\x12\x08\n\x04LIST\x10\x06\x12\x08\n\x04\x46ILE\x10\x07\x12\t\n\x05IMAGE\x10\x08\x12\t\n\x05\x41UDIO\x10\t\x12\t\n\x05VIDEO\x10\n\x12\x0c\n\x08\x44\x41TETIME\x10\x0b\x12\t\n\x05\x45MAIL\x10\x0c\x32\xf0\x01\n\nController\x12\x63\n\x0cRegisterTool\x12(.npi.core.controller.RegisterToolRequest\x1a).npi.core.controller.RegisterToolResponse\x12@\n\x0eUnregisterTool\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\x12;\n\tHeartbeat\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.EmptyB\x1eZ\x1cgithub.com/npi-ai/npi/serverb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'controller_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z\034github.com/npi-ai/npi/server'
  _globals['_LANGUAGE']._serialized_start=1115
  _globals['_LANGUAGE']._serialized_end=1171
  _globals['_PARAMETERTYPE']._serialized_start=1174
  _globals['_PARAMETERTYPE']._serialized_end=1336
  _globals['_REGISTERTOOLREQUEST']._serialized_start=70
  _globals['_REGISTERTOOLREQUEST']._serialized_end=180
  _globals['_REGISTERTOOLRESPONSE']._serialized_start=182
  _globals['_REGISTERTOOLRESPONSE']._serialized_end=219
  _globals['_UNREGISTERTOOLREQUEST']._serialized_start=221
  _globals['_UNREGISTERTOOLREQUEST']._serialized_end=256
  _globals['_HEARTBEATREQUEST']._serialized_start=258
  _globals['_HEARTBEATREQUEST']._serialized_end=288
  _globals['_TOOLSPEC']._serialized_start=290
  _globals['_TOOLSPEC']._serialized_end=407
  _globals['_METADATA']._serialized_start=409
  _globals['_METADATA']._serialized_end=519
  _globals['_FUNCTIONSPEC']._serialized_start=522
  _globals['_FUNCTIONSPEC']._serialized_end=688
  _globals['_RUNTIME']._serialized_start=690
  _globals['_RUNTIME']._serialized_end=780
  _globals['_DEPENDENCY']._serialized_start=782
  _globals['_DEPENDENCY']._serialized_end=825
  _globals['_FUNCTION']._serialized_start=828
  _globals['_FUNCTION']._serialized_end=974
  _globals['_PARAMETER']._serialized_start=976
  _globals['_PARAMETER']._serialized_end=1071
  _globals['_FEWSHOT']._serialized_start=1073
  _globals['_FEWSHOT']._serialized_end=1113
  _globals['_CONTROLLER']._serialized_start=1339
  _globals['_CONTROLLER']._serialized_end=1579
# @@protoc_insertion_point(module_scope)