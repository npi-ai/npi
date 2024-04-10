package main

import (
	"context"
	"github.com/fatih/color"
	"github.com/google/uuid"
	api "github.com/npi-ai/npi/proto/go/api"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"log"
	"os"
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
			doRequest("google-calendar", args[0])
		},
	}
	return cmd
}

func doRequest(app, instruction string) {
	var opts []grpc.DialOption
	opts = append(opts, grpc.WithTransportCredentials(insecure.NewCredentials()))
	conn, err := grpc.Dial(cfg.NPIServer, opts...)
	if err != nil {
		log.Fatalf("fail to dial: %v", err)
	}
	defer conn.Close()
	handle := api.NewChatServerClient(conn)
	cli, err := handle.Chat(context.Background())
	if err != nil {
		handleError(app, err)
	}
	err = cli.Send(&api.ChatRequest{
		RequestId:   uuid.NewString(),
		AppType:     api.AppType_GOOGLE_CALENDAR,
		Instruction: instruction,
		ThreadId:    uuid.NewString(),
	})
	if err != nil {
		handleError(app, err)
	}

	resp, err := cli.Recv()
	if err != nil {
		handleError(app, err)
	}
	color.Green(resp.Message)
}

func handleError(app string, err error) {
	color.Red("failed to chat with [%s]: %v", app, err)
	os.Exit(-1)
}
