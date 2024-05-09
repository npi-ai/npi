package main

import (
	"bufio"
	"context"
	"fmt"
	"github.com/fatih/color"
	"github.com/google/uuid"
	api "github.com/npi-ai/proto/go/api"
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
	}
	cmd.AddGroup()
	cmd.AddCommand(
		gmailCommand(),
		googleCalenderCommand(),
		githubCommand(),
		discordCommand(),
		twitterCommand(),
		webBrowserCommand(),
	)
	return cmd
}

func gmailCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "gmail",
		Short: "chat with Gmail",
		Run: func(cmd *cobra.Command, args []string) {
			doRequest(api.AppType_GOOGLE_GMAIL, args[0])
		},
	}
	return cmd
}

func googleCalenderCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "google-calendar",
		Aliases: []string{"gcal"},
		Short:   "chat with Google Calendar, alias: gcal",
		Run: func(cmd *cobra.Command, args []string) {
			doRequest(api.AppType_GOOGLE_CALENDAR, args[0])
		},
	}
	return cmd
}

func githubCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "github",
		Aliases: []string{"gcal"},
		Short:   "chat with Google Calendar, alias: gcal",
		Run: func(cmd *cobra.Command, args []string) {
			doRequest(api.AppType_GITHUB, args[0])
		},
	}
	return cmd
}

func twitterCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "twitter",
		Aliases: []string{"gcal"},
		Short:   "chat with Twitter",
		Run: func(cmd *cobra.Command, args []string) {
			doRequest(api.AppType_TWITTER, args[0])
		},
	}
	return cmd
}

func discordCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "discord",
		Aliases: []string{"gcal"},
		Short:   "chat with Discord",
		Run: func(cmd *cobra.Command, args []string) {
			doRequest(api.AppType_DISCORD, args[0])
		},
	}
	return cmd
}

func webBrowserCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "browser",
		Short: "chat with Web Browser",
		Run: func(cmd *cobra.Command, args []string) {
			doRequest(api.AppType_WEB_BROWSER, args[0])
		},
	}
	return cmd
}

func doRequest(app api.AppType, instruction string) {
	var opts []grpc.DialOption
	opts = append(opts, grpc.WithTransportCredentials(insecure.NewCredentials()))
	conn, err := grpc.Dial(cfg.GetGRPCEndpoint(), opts...)
	if err != nil {
		log.Fatalf("fail to dial: %v", err)
	}
	defer conn.Close()
	cli := api.NewAppServerClient(conn)
	resp, err := cli.Chat(context.Background(), &api.Request{
		Code:      api.RequestCode_CHAT,
		RequestId: uuid.New().String(),
		Request: &api.Request_ChatRequest{
			ChatRequest: &api.ChatRequest{
				Type:        app,
				Instruction: instruction,
			},
		},
	})
	if err != nil {
		handleError(app, err)
	}
	for {
		var req *api.Request
		switch resp.GetCode() {
		case api.ResponseCode_FINISHED:
			color.Green("Answer: %s", resp.GetChatResponse().GetMessage())
			return
		case api.ResponseCode_FAILED:
			color.Red("Failed: %s", resp.GetChatResponse().GetMessage())
			return
		case api.ResponseCode_MESSAGE:
			if resp.GetChatResponse().GetMessage() != "" {
				color.Yellow("Message: %s", resp.GetChatResponse().GetMessage())
			}
			fallthrough
		case api.ResponseCode_SUCCESS:
			rid := uuid.New().String()
			req = &api.Request{
				Code:      api.RequestCode_FETCH,
				RequestId: rid,
				ThreadId:  resp.ThreadId,
				Request: &api.Request_ChatRequest{
					ChatRequest: &api.ChatRequest{
						Type:        app,
						Instruction: instruction,
					},
				},
			}
		case api.ResponseCode_ACTION_REQUIRED:
			ar := resp.GetActionResponse()
			arr := &api.ActionResultRequest{
				ActionId: ar.GetActionId(),
			}
			switch ar.GetType() {
			case api.ActionType_INFORMATION:
				fmt.Printf("Action Required: Need more information.\n\n")
				fmt.Printf("Request for: %s\n", ar.Message)

				reader := bufio.NewReader(os.Stdin)
				arr.ActionResult, _ = reader.ReadString('\n')
				if err != nil {
					handleError(app, err)
				}
			case api.ActionType_CONFIRMATION:
				fmt.Printf("Action Required: Human Approve Action.\n\n")
				fmt.Printf("Request for: %s\n\n", ar.Message)
				fmt.Printf("Do you approve this action? [y/n]: ")

				reader := bufio.NewReader(os.Stdin)
				result, _ := reader.ReadString('\n')
				if result == "y\n" {
					arr.ActionResult = "approved"
				} else {
					arr.ActionResult = "denied"
				}
				req = &api.Request{
					Code:      api.RequestCode_ACTION_RESULT,
					RequestId: uuid.New().String(),
					ThreadId:  resp.ThreadId,
					Request: &api.Request_ActionResultRequest{
						ActionResultRequest: arr,
					},
				}
			}
		}
		resp, err = cli.Chat(context.Background(), req)
		if err != nil {
			handleError(app, err)
		}
	}

}

func handleError(app api.AppType, err error) {
	color.Red("failed to chat with [%s]: %v", app, err)
	os.Exit(-1)
}
