package main

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v3"
)

type CMDConfig struct {
	NPIServer string `yaml:"endpoint"`
	gRPCPort  int32  `yaml:"grpc_port"`
	httpPort  int32  `yaml:"http_port"`
	APIKey    string `yaml:"apiKey"`
}

func (c *CMDConfig) GetGRPCEndpoint() string {
	if c.gRPCPort == 0 {
		c.gRPCPort = 9140
	}
	return fmt.Sprintf("%s:%d", c.NPIServer, c.gRPCPort)
}

func (c *CMDConfig) GetHTTPEndpoint() string {
	if c.httpPort == 0 {
		c.httpPort = 9141
	}
	if c.NPIServer == "" {
		c.NPIServer = "127.0.0.1"
	}
	return fmt.Sprintf("%s:%d", c.NPIServer, c.httpPort)
}

func connectCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "connect",
		Short: "connect to NPI server",
	}

	cmd.AddCommand(connectTestCommand())
	//cmd.AddCommand(connectAuthCommand())

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
				resp, err := httpClient.R().Get("/ping")
				if err != nil {
					if time.Since(start) < 30*time.Second {
						time.Sleep(1 * time.Second)
						continue
					}
					color.Red("failed to connect NPi Server: %v", err)
					os.Exit(-1)
				}
				if resp.StatusCode() == 200 {
					break
				}

				color.Red("Connected to NPi Server, but server returned: %d", resp.StatusCode())
				os.Exit(-1)
			}

			_, _ = color.New(color.FgGreen, color.Bold).Println("NPi Server is operational!")
		},
	}
	return cmd
}

func connectAuthCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "connect auth",
		Short: "Authorizing to access NPI server",
		Run: func(cmd *cobra.Command, args []string) {
			if cfg.APIKey == "" {
				color.Red("apiKey is required")
				os.Exit(-1)
			}

			defaultConfigPath := filepath.Join(configHome, ".npiai")
			_, err := os.Stat(defaultConfigPath)
			if err != nil {
				if !os.IsNotExist(err) {
					color.Red("failed to get config dir: %v ", err)
					os.Exit(-1)
				}
				err = os.MkdirAll(defaultConfigPath, 0755)
				if err != nil {
					color.Red("failed to create config dir: %v ", err)
					os.Exit(-1)
				}
			}
			f, err := os.Create(filepath.Join(defaultConfigPath, "config.yaml"))
			if err != nil {
				color.Red("failed to open config file: %v ", err)
				os.Exit(-1)
			}
			data, _ := yaml.Marshal(&cfg)
			_, err = f.Write(data)
			if err != nil {
				color.Red("failed to write config file: %v ", err)
				os.Exit(-1)
			}
		},
	}
	cmd.Flags().StringVar(&cfg.NPIServer, "endpoint", "localhost", "the endpoint of NPI Server")
	cmd.Flags().Int32Var(&cfg.gRPCPort, "grpc-port", 9140, "the port of gRPC Server")
	cmd.Flags().Int32Var(&cfg.httpPort, "http-port", 9141, "the port of HTTP Server")
	cmd.Flags().StringVar(&cfg.APIKey, "apiKey", "", "the api key for NPI Server")
	return cmd
}
