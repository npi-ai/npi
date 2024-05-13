package main

import (
	"io"
	"os"
	"strconv"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v3"
)

func configCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config",
		Short: "configure global parameters of the NPi CLI",
	}
	cmd.AddCommand(setCommand())
	cmd.AddCommand(getCommand())
	cmd.AddCommand(showCommand())
	return cmd
}

func setCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "set [key] [value]",
		Short: "set the value by key",
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) != 2 {
				_ = cmd.Help()
				return
			}
			cmdCfg := loadCfg()
			switch args[0] {
			case "api-key":
				cmdCfg.APIKey = args[1]
			case "endpoint":
				cmdCfg.NPIServer = args[1]
			case "insecure":
				v, err := strconv.ParseBool(args[1])
				if err != nil {
					color.Red("failed to parse boolean value: %v", err)
					return
				}
				cmdCfg.Insecure = v
			default:
				color.Red("unknown key: %s", args[0])
			}
			f, err := os.OpenFile(makeSureConfigFileExist(), os.O_CREATE|os.O_WRONLY, 0644)
			if err != nil {
				color.Red("failed to open config file: %v", err)
				return
			}

			data, _ := yaml.Marshal(cmdCfg)
			_, _ = f.Write(data)
			_ = f.Close()
		},
	}
	return cmd
}

func getCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get [key]",
		Short: "get the value by key",
		Run: func(cmd *cobra.Command, args []string) {
			cmdCfg := loadCfg()
			switch args[0] {
			case "api-key":
				color.Green("api-key = %s", cmdCfg.APIKey)
			case "endpoint":
				color.Green("endpoint = %s", cmdCfg.GetGRPCEndpoint())
			case "insecure":
				color.Green("insecure = %v", cmdCfg.Insecure)
			default:
				color.Red("unknown key: %s", args[0])
			}
		},
	}
	return cmd
}

func showCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show",
		Short: "show all configuration of NPi Client",
		Run: func(cmd *cobra.Command, args []string) {
			cmdCfg := loadCfg()
			data, _ := yaml.Marshal(cmdCfg)
			color.Green(string(data))
		},
	}

	return cmd
}

func loadCfg() *CMDConfig {
	f, err := os.Open(makeSureConfigFileExist())
	if err != nil {
		if os.IsNotExist(err) {
			return &CMDConfig{
				Insecure: true,
			}
		}
		color.Red("failed to open config file: %v", err)
		os.Exit(-1)
	}
	cmdCfg := &CMDConfig{}
	data, _ := io.ReadAll(f)
	err = yaml.Unmarshal(data, cmdCfg)
	if err != nil {
		color.Red("failed to unmarshal config file: %v", err)
		os.Exit(-1)
	}
	return cmdCfg
}
