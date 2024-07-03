package main

import (
	"context"
	"flag"
	"fmt"
	"net/http"
	"os"
	"strings"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	gw "github.com/npi-ai/playground/go" // Update
	"github.com/rs/cors"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/grpclog"
)

var (
	// command-line options:
	// gRPC server endpoint
	grpcServerEndpoint = flag.String("grpc-server-endpoint", "127.0.0.1:9140", "gRPC server endpoint")
)

func run() error {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	headerMatcher := func(key string) (string, bool) {
		switch strings.ToUpper(key) {
		case "X-NPI-TOKEN", "USER-AGENT", "ACCEPT", "ACCESS-CONTROL-ALLOW-ORIGIN'":
			return key, true
		default:
			return runtime.DefaultHeaderMatcher(key)
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

	err := gw.RegisterPlaygroundHandlerFromEndpoint(ctx, mux, *grpcServerEndpoint, opts)
	if err != nil {
		return err
	}

	withCors := cors.New(cors.Options{
		AllowOriginFunc: func(origin string) bool {
			return true
		},
		AllowedMethods: []string{"GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"},
		// "ACCEPT", "Authorization", "Content-Type", "USER-AGENT", "X-NPI-TOKEN"
		AllowedHeaders: []string{"*"},
		//ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		AllowedOrigins: []string{
			"*",
		},
		MaxAge: 300,
	}).Handler(mux)
	// Start HTTP server (and proxy calls to gRPC server endpoint)
	fmt.Printf("Starting HTTP server on port 8081, endpoint: %s", *grpcServerEndpoint)
	return http.ListenAndServe(":8081", withCors)
}

func main() {
	flag.Parse()

	if err := run(); err != nil {
		grpclog.Fatal(err)
	}
}
