package main

import (
	"github.com/spf13/cobra"
)

func newConnectCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "connect",
		Short: "connect to NPI server",
		Run: func(cmd *cobra.Command, args []string) {

		},
	}
	return cmd
}
