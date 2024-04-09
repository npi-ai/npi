package main

import (
	"os"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

const (
	cliName        = "npi"
	cliDescription = "the appCommand-line tool for NPi"
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
	rootCmd.AddCommand(
		connectCommand(),
		appCommand(),
		versionCommand(),
	)
	rootCmd.CompletionOptions.DisableDefaultCmd = true
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
