NPI_PROTO_ROOT=$(shell pwd)

generate-py:
	mkdir -p ${NPI_PROTO_ROOT}/proto
	python -m grpc_tools.protoc -I=${NPI_PROTO_ROOT}/include \
		  -I=${NPI_PROTO_ROOT} \
 		 --python_out=${NPI_PROTO_ROOT}/proto \
 		 --pyi_out=${NPI_PROTO_ROOT}/proto \
 		 --grpc_python_out=${NPI_PROTO_ROOT}/proto playground.proto

generate-http:
	mkdir -p ${NPI_PROTO_ROOT}/http
	protoc -I=${NPI_PROTO_ROOT}/include -I=${NPI_PROTO_ROOT} \
		  --grpc-gateway_opt paths=source_relative \
		  --grpc-gateway_opt generate_unbound_methods=true \
		  --grpc-gateway_out ${NPI_PROTO_ROOT}/http \
		  --openapiv2_out ${NPI_PROTO_ROOT}/http playground.proto
