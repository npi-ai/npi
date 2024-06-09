package main

import (
	"context"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/fatih/color"
	api "github.com/npi-ai/npi/proto/go/api"
	"github.com/pkg/browser"
	"github.com/spf13/cobra"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
)

func authCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "auth",
		Short: "authorize target applications",
	}
	cmd.PersistentFlags().BoolVar(&cfg.UseProvisionedSecret, "use-provision", false, "if use NPi Playground provisioned secret")
	cmd.AddCommand(authGoogleCommand())
	cmd.AddCommand(authGitHubCommand())
	cmd.AddCommand(authDiscordCommand())
	cmd.AddCommand(authTwitterCommand())
	cmd.AddCommand(authTwilioCommand())
	return cmd
}

var (
	googleSecretFile string
)

func authGoogleCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "google [app_name]",
		Short: "authorize Google API: gmail, calendar",
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) == 0 {
				_ = cmd.Help()
				return
			}
			var resp *api.AuthorizeResponse
			var err error
			cred := map[string]string{
				"callback": "http://localhost:19141/auth/google/callback",
			}
			if !cfg.UseProvisionedSecret {
				if googleSecretFile == "" {
					_ = cmd.Help()
					return
				}
				f, err := os.Open(googleSecretFile)
				if err != nil {
					color.Red("failed to open Google secret file: %v", err)
					os.Exit(-1)
				}
				defer f.Close()
				data, err := io.ReadAll(f)
				if err != nil {
					color.Red("failed to read Google secret file: %v", err)
					os.Exit(-1)
				}
				cred["secrets"] = string(data)
			} else {
				cred["npi-provisioned-config"] = "true"
			}
			if args[0] == "gmail" {
				resp, err = doAuthRequest(api.AppType_GOOGLE_GMAIL, cred)
			} else {
				resp, err = doAuthRequest(api.AppType_GOOGLE_CALENDAR, cred)
			}
			if err != nil {
				color.Red("failed to authorize Google: %v", err)
				os.Exit(-1)
			}
			redirectUrl, exist := resp.Result["url"]
			if !exist {
				color.Green("authorization success")
				os.Exit(0)
			}
			color.Green("please finish the authorization in the browser...")
			errChan := make(chan error)
			go server(context.Background(), errChan)
			err = browser.OpenURL(redirectUrl)
			err = <-errChan
			if err != nil {
				color.Red("failed to authorization: %v", err)
				os.Exit(-1)
			}
			close(errChan)
			time.Sleep(1 * time.Second)
		},
	}
	cmd.Flags().StringVar(&googleSecretFile, "secret-file", "", "the secret file for Google API")
	return cmd
}

func server(_ context.Context, ch chan error) {
	http.HandleFunc("/auth/google/callback", oauthCallback(ch))
	if err := http.ListenAndServe(":19141", nil); err != nil {
		color.Red("failed to start consent server: %v", err)
	}
}

func oauthCallback(ch chan error) func(w http.ResponseWriter, r *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		queryParams := r.URL.Query()
		conn := getGRPCConn()
		defer conn.Close()
		cli := api.NewAppServerClient(conn)
		m := map[string]string{
			"state":    queryParams.Get("state"),
			"code":     queryParams.Get("code"),
			"callback": "http://localhost:19141/auth/google/callback",
		}
		_, err := cli.GoogleAuthCallback(getMetadata(context.Background()), &api.AuthorizeRequest{
			Credentials: m,
		})
		if err != nil {
			ch <- err
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("authorize success, please close window"))
		color.Green("authorization success")
		ch <- nil
	}
}

var (
	accessToken string
)

func authGitHubCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "github",
		Short: "authorize GitHub",
		Run: func(cmd *cobra.Command, args []string) {
			if accessToken == "" {
				_ = cmd.Help()
				return
			}
			_, err := doAuthRequest(api.AppType_GITHUB, map[string]string{
				"access_token": accessToken,
			})

			if err != nil {
				color.Red("failed to authorize GitHub: %v", err)
				os.Exit(-1)
			}
			color.Green("authorization success")
		},
	}

	cmd.Flags().StringVar(&accessToken, "access-token", "", "the personal access token for GitHub")

	return cmd
}

func authDiscordCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "discord",
		Short: "authorize Discord",
		Run: func(cmd *cobra.Command, args []string) {
			if accessToken == "" {
				_ = cmd.Help()
				return
			}
			_, err := doAuthRequest(api.AppType_DISCORD, map[string]string{
				"access_token": accessToken,
			})
			if err != nil {
				color.Red("failed to authorize Discord: %v", err)
				os.Exit(-1)
			}
			color.Green("authorization success")
		},
	}
	cmd.Flags().StringVar(&accessToken, "access-token", "", "the access token for Discord")

	return cmd
}

var (
	twitterUsername = ""
	twitterPassword = ""
)

func authTwitterCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "twitter",
		Short: "authorize Twitter",
		Run: func(cmd *cobra.Command, args []string) {
			if twitterUsername == "" || twitterPassword == "" {
				color.Yellow("username and password are required")
				_ = cmd.Help()
				return
			}
			_, err := doAuthRequest(api.AppType_TWITTER, map[string]string{
				"username": twitterUsername,
				"password": twitterPassword,
			})
			if err != nil {
				color.Red("failed to authorize Twitter: %v", err)
				os.Exit(-1)
			}
			color.Green("authorization success")
		},
	}
	cmd.Flags().StringVar(&twitterUsername, "username", "", "the username of your Twitter/X account")
	cmd.Flags().StringVar(&twitterPassword, "password", "", "the password of your Twitter/X account")

	return cmd
}

var (
	twilioAccount = ""
	twilioToken   = ""
	twilioFrom    = ""
)

func authTwilioCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "twilio",
		Short: "authorize Twilio",
		Run: func(cmd *cobra.Command, args []string) {
			if twilioAccount == "" || twilioToken == "" || twilioFrom == "" {
				color.Yellow("account/token/from required")
				_ = cmd.Help()
				return
			}

			_, err := doAuthRequest(api.AppType_TWILIO, map[string]string{
				"from_phone_number": twilioFrom,
				"account_sid":       twilioAccount,
				"auth_token":        twilioToken,
			})

			if err != nil {
				color.Red("failed to authorize Twilio: %v", err)
				os.Exit(-1)
			}
			color.Green("authorization success")
		},
	}
	cmd.Flags().StringVar(&twilioAccount, "account", "", "The Twilio Account ID")
	cmd.Flags().StringVar(&twilioToken, "token", "", "The Twilio Auth Token")
	cmd.Flags().StringVar(&twilioFrom, "from", "", "Twilio phone number to send from")

	return cmd
}

func doAuthRequest(app api.AppType, params map[string]string) (*api.AuthorizeResponse, error) {
	conn := getGRPCConn()
	defer conn.Close()
	cli := api.NewAppServerClient(conn)
	return cli.Authorize(getMetadata(context.Background()), &api.AuthorizeRequest{
		Type:        app,
		Credentials: params,
	})
}

func getGRPCConn() *grpc.ClientConn {
	var opts []grpc.DialOption
	if !cfg.Secure {
		opts = append(opts, grpc.WithTransportCredentials(insecure.NewCredentials()))
	} else {
		opts = append(opts, grpc.WithTransportCredentials(credentials.NewClientTLSFromCert(nil, "")))
	}
	conn, err := grpc.Dial(cfg.GetGRPCEndpoint(), opts...)
	if err != nil {
		log.Fatalf("fail to dial: %v", err)
	}
	return conn
}
