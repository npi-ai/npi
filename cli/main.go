package main

import (
	"os"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

const (
	cliName        = "npi"
	cliDescription = "the command-line tool for NPi"
)

var (
	rootCmd = &cobra.Command{
		Use:        cliName,
		Short:      cliDescription,
		SuggestFor: []string{"npi"},
	}
)

func init() {
	cobra.EnablePrefixMatching = true
	cobra.EnableCommandSorting = false

	rootCmd.PersistentPreRun = func(cmd *cobra.Command, args []string) {
		cmdCfg := loadCfg()
		cfg.merge(rootCmd.PersistentFlags(), *cmdCfg)
		err := checkUpdate()
		if err != nil {
			color.Yellow("failed to check updating: %v ", err)
			return
		}
		if cmd.Name() == "connect" || cmd.Name() == "version" {
			return
		}
	}
	rootCmd.PersistentFlags().StringVar(&cfg.NPIServer, "endpoint", "127.0.0.1:9140", "the endpoint of NPi server")
	rootCmd.PersistentFlags().StringVar(&cfg.APIKey, "api-key", "", "the api access key for NPi server")
	rootCmd.PersistentFlags().BoolVar(&cfg.Secure, "secure", false, "if using secure connection")
	rootCmd.CompletionOptions.DisableDefaultCmd = true
	rootCmd.AddCommand(
		authCommand(),
		connectCommand(),
		appCommand(),
		versionCommand(),
		configCommand(),
	)
}

func main() {
	MustStart()
}

func Start() error {
	return rootCmd.Execute()
}

func MustStart() {
	if err := Start(); err != nil {
		color.Red("npi run error: %s", err)
		os.Exit(-1)
	}
}
