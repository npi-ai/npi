package main

import (
	"context"
	"flag"
	"fmt"
	"google.golang.org/grpc/metadata"
	"net/http"
	"os"
	"strings"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"github.com/npi-ai/npi/server/service"
	gw "github.com/npi-ai/playground/go"
	"github.com/rs/cors"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"gopkg.in/yaml.v3"
)

var (
	grpcServerEndpoint string
)

type ProxyController struct {
	authNPi2App *mongo.Collection
	userAuth    *mongo.Collection
	appSvc      *service.AppService
}

func (pc *ProxyController) run() error {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	headerMatcher := func(key string) (string, bool) {
		switch strings.ToUpper(key) {
		case "X-NPI-TOKEN", "X-NPIAI-ORG-ID", "USER-AGENT", "ACCEPT", "ACCESS-CONTROL-ALLOW-ORIGIN'":
			return strings.ToUpper(key), true
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
			// 0. auth
			// 1. search instance
			md, ok := metadata.FromOutgoingContext(ctx)
			if !ok {
				return status.Error(codes.InvalidArgument, "invalid metadata")
			}

			orgID, err := primitive.ObjectIDFromHex(md.Get("x-npiai-org-id")[0])
			if err != nil {
				return status.Error(codes.InvalidArgument, "invalid x-npiai-org-id")
			}
			appCli, err := pc.appSvc.GetOrCreateOrgDefaultAppClient(ctx, orgID)
			if err != nil {
				return status.Error(codes.Internal, "internal error")
			}

			// 2. set authorization
			if method == gw.Playground_Chat_FullMethodName {
				_req, ok := req.(*gw.Request)
				if !ok {
					return status.Error(codes.InvalidArgument, "invalid request")
				}

				needAuth := true
				if _req.GetChatRequest() != nil {
					var permID int
					switch _req.GetChatRequest().Type {
					case gw.AppType_GOOGLE_GMAIL:
						permID = model.AppGoogleGmailAll.PermissionID
					case gw.AppType_GOOGLE_CALENDAR:
						permID = model.AppGoogleCalendarAll.PermissionID
					case gw.AppType_GITHUB:
						permID = model.AppGitHubAll.PermissionID
					case gw.AppType_SLACK:
						permID = model.AppSlackAll.PermissionID
					case gw.AppType_DISCORD:
						permID = model.AppDiscordAll.PermissionID
					case gw.AppType_TWILIO:
						permID = model.AppTwilioAll.PermissionID
					case gw.AppType_TWITTER:
						permID = model.AppXComAll.PermissionID
					default:
						needAuth = false
					}
					uAuth := model.UserAuthorization{}
					if needAuth {
						result := pc.authNPi2App.FindOne(ctx, bson.M{
							"app_id":     appCli.ID,
							"permission": permID,
						})
						println(appCli.ID.Hex())
						if result.Err() != nil {
							return status.Error(codes.Unauthenticated, "")
						}

						auth := model.AuthNPIToApp{}
						if err = result.Decode(&auth); err != nil {
							log.Warn(ctx).Err(err).Msg("decode authorization")
							return status.Error(codes.Internal, "internal error")
						}

						result = pc.userAuth.FindOne(ctx, bson.M{
							"_id": auth.AuthID,
						})

						if result.Err() != nil {
							return status.Error(codes.Internal, "")
						}

						if err = result.Decode(&uAuth); err != nil {
							log.Warn(ctx).Err(err).Msg("decode UserAuthorization")
							return status.Error(codes.Internal, "internal error")
						}
					}
					_req.Authorization = uAuth.Authorization()
					req = _req
				}
			}
			return invoker(ctx, method, req, reply, cc, opts...)
		}))

	err := gw.RegisterPlaygroundHandlerFromEndpoint(ctx, mux, grpcServerEndpoint, opts)
	if err != nil {
		return err
	}

	withCors := cors.New(cors.Options{
		AllowOriginFunc: func(origin string) bool {
			return true
		},
		AllowedMethods:   []string{"GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"*"},
		AllowCredentials: true,
		AllowedOrigins: []string{
			"*",
		},
		MaxAge: 300,
	}).Handler(mux)

	fmt.Printf("Starting HTTP server on port 8081\n")
	return http.ListenAndServe(":8081", withCors)
}

func main() {
	flag.Parse()
	log.Info().Str("Config", os.Getenv("DB_CONFIG")).Msg("--- Config ---")
	log.Info().Str("Endpoint", os.Getenv("ENDPOINT")).Msg("--- Config ---")
	data, err := os.ReadFile(os.Getenv("DB_CONFIG"))
	if err != nil {
		panic(err)
	}
	dbCfg := db.MongoConfig{}
	_ = yaml.Unmarshal(data, &dbCfg)
	db.InitMongoDB(context.Background(), dbCfg)
	pc := &ProxyController{
		appSvc:      service.NewAppService(),
		authNPi2App: db.GetCollection(db.CollAuthNPIToApp),
		userAuth:    db.GetCollection(db.CollUserAuthorization),
	}
	grpcServerEndpoint = os.Getenv("ENDPOINT")
	if grpcServerEndpoint == "" {
		grpcServerEndpoint = "localhost:9140"
	}
	if err = pc.run(); err != nil {
		panic(err)
	}
}
