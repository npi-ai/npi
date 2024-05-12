module github.com/npi-ai/npi/cli

go 1.21

require (
	github.com/fatih/color v1.16.0
	github.com/go-resty/resty/v2 v2.12.0
	github.com/google/uuid v1.6.0
	github.com/npi-ai/npi/proto/go v0.0.0
	github.com/pkg/browser v0.0.0-20240102092130-5ac0b6a4141c
	github.com/spf13/cobra v1.8.0
	google.golang.org/grpc v1.63.2
	gopkg.in/yaml.v3 v3.0.1
)

replace (
	github.com/npi-ai/npi/proto/go  => ../proto/go
)

require (
	github.com/inconshreveable/mousetrap v1.1.0 // indirect
	github.com/mattn/go-colorable v0.1.13 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/spf13/pflag v1.0.5 // indirect
	go.uber.org/mock v0.4.0 // indirect
	golang.org/x/net v0.22.0 // indirect
	golang.org/x/sys v0.18.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20240227224415-6ceb2ff114de // indirect
	google.golang.org/protobuf v1.33.0 // indirect
)
