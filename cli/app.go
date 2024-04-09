package main

import (
	"errors"
	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"os"
)

var (
	task string
)

func appCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "app",
		Short: "the applications NPi supported",
		Run: func(cmd *cobra.Command, args []string) {

		},
	}
	cmd.AddGroup()
	cmd.AddCommand(
		gmailCommand(),
		googleCalenderCommand(),
	)
	cmd.PersistentFlags().StringVar(&task, "task", "", "the task you want to do")
	return cmd
}

func gmailCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "gmail",
		Short: "chat with Gmail",
		Run: func(cmd *cobra.Command, args []string) {

		},
	}
	return cmd
}

func googleCalenderCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "google-calendar",
		Aliases: []string{"gcal"},
		Short:   "chat with Google Calendar",
		Run: func(cmd *cobra.Command, args []string) {
			doRequest("google-calendar", task)
		},
	}
	return cmd
}

func doRequest(app, instruction string) {
	resp, err := httpClient.R().SetBody(map[string]interface{}{
		"app":         app,
		"instruction": instruction,
	}).Post("/chat")
	if err != nil {
		handleError(app, err)
	}
	if resp.StatusCode() != 200 {
		handleError(app, errors.New("response not 200"))
	}
	color.Green(string(resp.Body()))
}

func handleError(app string, err error) {
	color.Red("failed to chat with [%s]: %v", app, err)
	os.Exit(-1)
}
