NPI_PROTO_ROOT=$(shell pwd)

generate-go:
	mkdir -p ${NPI_PROTO_ROOT}/go
	protoc -I=${NPI_PROTO_ROOT}/include \
          -I=${NPI_PROTO_ROOT} \
          --go_out=${NPI_PROTO_ROOT}/go \
	  --go_opt=paths=source_relative \
	  --go-grpc_out=${NPI_PROTO_ROOT}/go \
	  --go-grpc_opt=paths=source_relative,require_unimplemented_servers=false \
	  --go-grpc-mock_out=${NPI_PROTO_ROOT}/go \
	  --go-grpc-mock_opt=paths=source_relative \
	  ${NPI_PROTO_ROOT}/api/api.proto


generate-py:
	mkdir -p ${NPI_PROTO_ROOT}/python
	python -m grpc_tools.protoc -I=${NPI_PROTO_ROOT}/include \
		  -I=${NPI_PROTO_ROOT} \
 		 --python_out=${NPI_PROTO_ROOT}/python \
 		 --pyi_out=${NPI_PROTO_ROOT}/python \
 		 --grpc_python_out=${NPI_PROTO_ROOT}/python \
 		  ${NPI_PROTO_ROOT}/api/api.proto
