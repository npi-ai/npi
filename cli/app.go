package main

import (
	"bufio"
	"context"
	"fmt"
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
			doRequest(api.AppType_GOOGLE_CALENDAR, args[0])
		},
	}
	return cmd
}

func doRequest(app api.AppType, instruction string) {
	var opts []grpc.DialOption
	opts = append(opts, grpc.WithTransportCredentials(insecure.NewCredentials()))
	conn, err := grpc.Dial(cfg.NPIServer, opts...)
	if err != nil {
		log.Fatalf("fail to dial: %v", err)
	}
	defer conn.Close()
	cli := api.NewChatServerClient(conn)
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
		switch resp.GetCode() {
		case api.ResponseCode_FINISHED:
			color.Green("Answer: %s", resp.GetChatResponse().GetMessage())
			return
		case api.ResponseCode_FAILED:
			color.Green("Failed: %s", resp.GetChatResponse().GetMessage())
			return
		case api.ResponseCode_MESSAGE:
			if resp.GetChatResponse().GetMessage() != "" {
				color.Yellow("Message: %s", resp.GetChatResponse().GetMessage())
			}
			fallthrough
		case api.ResponseCode_SUCCESS:
			rid := uuid.New().String()
			println(rid)
			resp, err = cli.Chat(context.Background(), &api.Request{
				Code:      api.RequestCode_FETCH,
				RequestId: rid,
				ThreadId:  resp.ThreadId,
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
		case api.ResponseCode_ACTION_REQUIRED:
			ar := resp.GetActionResponse()
			switch ar.GetType() {
			case api.ActionType_HUMAN_FEEDBACK:
				fb := ar.GetHumanFeedback()
				arr := &api.ActionResultRequest{
					ActionId: ar.GetActionId(),
				}
				switch fb.GetType() {
				case api.HumanFeedbackActionType_INPUT:
					reader := bufio.NewReader(os.Stdin)
					fmt.Printf("Action Required: %s\n", fb.GetNotice())
					arr.ActionResult, _ = reader.ReadString('\n')
				}
				resp, err = cli.Chat(context.Background(), &api.Request{
					Code:      api.RequestCode_ACTION_RESULT,
					RequestId: uuid.New().String(),
					ThreadId:  resp.ThreadId,
					Request: &api.Request_ActionResultRequest{
						ActionResultRequest: arr,
					},
				})
				if err != nil {
					handleError(app, err)
				}
			case api.ActionType_SAFEGUARD:
				println("Action SAFEGUARD")
			}
			// skip
		}
	}

}

func handleError(app api.AppType, err error) {
	color.Red("failed to chat with [%s]: %v", app, err)
	os.Exit(-1)
}
