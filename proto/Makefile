NPI_PROTO_ROOT=$(shell pwd)

generate-go:
	mkdir -p ${NPI_PROTO_ROOT}/go
	protoc -I=${NPI_PROTO_ROOT}/include \
          -I=${NPI_PROTO_ROOT}/proto \
          --go_out=${NPI_PROTO_ROOT}/go/api \
	  --go_opt=paths=source_relative \
	  --go-grpc_out=${NPI_PROTO_ROOT}/go/api \
	  --go-grpc_opt=paths=source_relative,require_unimplemented_servers=false \
	  --go-grpc-mock_out=${NPI_PROTO_ROOT}/go/api \
	  --go-grpc-mock_opt=paths=source_relative \
	  	api.proto


generate-py:
	mkdir -p ${NPI_PROTO_ROOT}/python
	python -m grpc_tools.protoc -I=${NPI_PROTO_ROOT}/include \
		  -I=${NPI_PROTO_ROOT} \
		  -I=${NPI_PROTO_ROOT}/proto \
 		 --python_out=${NPI_PROTO_ROOT}/python/npiai_proto \
 		 --pyi_out=${NPI_PROTO_ROOT}/python/npiai_proto \
 		 --grpc_python_out=${NPI_PROTO_ROOT}/python/npiai_proto \
 		 api.proto
