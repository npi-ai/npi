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
		checkConfig()
		err := checkUpdate()
		if err != nil {
			color.Yellow("failed to check updating: %v ", err)
			return
		}
		if cmd.Name() == "connect" || cmd.Name() == "version" {
			return
		} else {
			readConfig()
		}
	}
	rootCmd.CompletionOptions.DisableDefaultCmd = true
	rootCmd.AddCommand(
		connectCommand(),
		appCommand(),
		versionCommand(),
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
