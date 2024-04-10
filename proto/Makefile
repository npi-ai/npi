NPI_PROTO_ROOT=$(shell pwd)

generate:
	mkdir -p ${NPI_PROTO_ROOT}/pkg
	protoc -I=${NPI_PROTO_ROOT}/include \
          -I=${NPI_PROTO_ROOT} \
          --go_out=${NPI_PROTO_ROOT}/pkg \
	  --go_opt=paths=source_relative \
	  --go-grpc_out=${NPI_PROTO_ROOT}/pkg \
	  --go-grpc_opt=paths=source_relative,require_unimplemented_servers=false \
	  --go-grpc-mock_out=${NPI_PROTO_ROOT}/pkg \
	  --go-grpc-mock_opt=paths=source_relative \
	  ${NPI_PROTO_ROOT}/api.proto

# TODO: https://buf.build/docs/configuration/v1/buf-gen-yaml