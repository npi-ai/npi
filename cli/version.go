package main

import (
	"encoding/json"
	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

var (
	Version   string
	GitCommit string
	BuildDate string
	Platform  string
)

func versionCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "version",
		Short: "get NPI version info",
		Run: func(cmd *cobra.Command, args []string) {
			info := map[string]string{
				"Version":   Version,
				"Platform":  Platform,
				"GitCommit": GitCommit,
				"BuildDate": BuildDate,
			}
			data, _ := json.MarshalIndent(info, "", "  ")
			color.Green(string(data))
		},
	}
	return cmd
}
