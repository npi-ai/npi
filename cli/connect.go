package main

import (
	"os"
	"path/filepath"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v3"
)

type CMDConfig struct {
	NPIServer string `yaml:"endpoint"`
	APIKey    string `yaml:"apiKey"`
}

func connectCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "connect",
		Short: "connect to NPI server",
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
	cmd.Flags().StringVar(&cfg.NPIServer, "endpoint", "localhost:9140", "the endpoint of NPI Server")
	cmd.Flags().StringVar(&cfg.APIKey, "apiKey", "", "the api key for NPI Server")
	return cmd
}
