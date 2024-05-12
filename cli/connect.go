package main

import (
	"context"
	api "github.com/npi-ai/npi/proto/go/api"
	"google.golang.org/protobuf/types/known/emptypb"
	"os"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

type CMDConfig struct {
	NPIServer string `yaml:"endpoint"`
	APIKey    string `yaml:"api-key"`
	Insecure  bool   `yaml:"insecure"`
}

func (c *CMDConfig) GetGRPCEndpoint() string {
	return c.NPIServer
}

func connectCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "connect",
		Short: "connect to NPI server",
	}

	cmd.AddCommand(connectTestCommand())
	return cmd
}

func connectTestCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "test",
		Short: "Testing if NPi Server is connected",
		Run: func(cmd *cobra.Command, args []string) {
			start := time.Now()
			color.White("Connecting to NPi Server...")
			color.New()
			for {
				conn := getGRPCConn()
				cli := api.NewAppServerClient(conn)

				_, err := cli.Ping(getMetadata(context.Background()), &emptypb.Empty{})
				if err != nil {
					if time.Since(start) < 30*time.Second {
						time.Sleep(1 * time.Second)
						continue
					}
					color.Red("failed to connect NPi Server: %v", err)
					os.Exit(-1)
				}
				break
			}

			_, _ = color.New(color.FgGreen, color.Bold).Println("NPi Server is operational!")
		},
	}
	return cmd
}
