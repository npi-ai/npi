package main

import (
	"context"
	"flag"
	"fmt"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/grpclog"
	"net/http"
	"os"
	"strings"

	gw "github.com/npi-ai/npi/proto/go/api" // Update
)

var (
	// command-line options:
	// gRPC server endpoint
	grpcServerEndpoint = flag.String("grpc-server-endpoint", "localhost:9140", "gRPC server endpoint")
)

func run() error {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	headerMatcher := func(key string) (string, bool) {
		switch strings.ToUpper(key) {
		case "X-NPI-TOKEN", "USER-AGENT", "ACCEPT":
			return key, true
		default:
			return key, false
		}
	}
	// Register gRPC server endpoint
	// Note: Make sure the gRPC server is running properly and accessible
	mux := runtime.NewServeMux(
		runtime.WithIncomingHeaderMatcher(headerMatcher),
	)
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	opts = append(opts, grpc.WithUnaryInterceptor(
		func(ctx context.Context, method string, req, reply interface{}, cc *grpc.ClientConn, invoker grpc.UnaryInvoker, opts ...grpc.CallOption) error {
			// just for debug
			return invoker(ctx, method, req, reply, cc, opts...)
		}))

	endpoint := os.Getenv("GRPC_SERVER_ENDPOINT")
	if endpoint != "" && *grpcServerEndpoint == "localhost:9140" {
		*grpcServerEndpoint = endpoint
	}

	err := gw.RegisterAppServerHandlerFromEndpoint(ctx, mux, *grpcServerEndpoint, opts)
	if err != nil {
		return err
	}

	// Start HTTP server (and proxy calls to gRPC server endpoint)
	fmt.Printf("Starting HTTP server on port 8081, endpoint: %s", *grpcServerEndpoint)
	return http.ListenAndServe(":8081", mux)
}

func main() {
	flag.Parse()

	if err := run(); err != nil {
		grpclog.Fatal(err)
	}
}
