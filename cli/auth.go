package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/fatih/color"
	"github.com/pkg/browser"
	"github.com/spf13/cobra"
	"io"
	"net/http"
	"os"
)

func authCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "auth",
		Short: "authorize target applications",
	}
	cmd.AddCommand(authGoogleCommand())
	cmd.AddCommand(authGitHubCommand())
	return cmd
}

var (
	googleSecretFile string
)

func authGoogleCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "google [app_name]",
		Short: "authorize Google API",
		Run: func(cmd *cobra.Command, args []string) {
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
			response, err := httpClient.R().SetBody(map[string]string{
				"secrets": string(data),
				"app":     args[0],
			}).Post("/auth/google")
			if err != nil {
				color.Red("failed to authorize Google API: %v", err)
				os.Exit(-1)
			}
			if response.StatusCode() != 200 {
				color.Red("failed to authorize Google API: %s", string(response.Body()))
				os.Exit(-1)
			}
			m := map[string]string{}
			_ = json.Unmarshal(response.Body(), &m)
			color.Green("please finish the authorization in the browser...")
			errChan := make(chan error)
			go server(context.Background(), "/auth/google/callback", errChan)
			err = browser.OpenURL(m["url"])
			err = <-errChan
			if err != nil {
				color.Red("failed to authorization: %v", err)
				os.Exit(-1)
			}
			close(errChan)
		},
	}
	cmd.Flags().StringVar(&googleSecretFile, "secret-file", "", "the secret file for Google API")
	return cmd
}

func server(_ context.Context, callbackURL string, ch chan error) {
	http.HandleFunc(callbackURL, oauthCallback(callbackURL, ch))
	if err := http.ListenAndServe(":19141", nil); err != nil {
		color.Red("failed to start consent server: %v", err)
	}
}

func oauthCallback(callbackURL string, ch chan error) func(w http.ResponseWriter, r *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		queryParams := r.URL.Query()
		resp, err := httpClient.R().SetQueryParams(map[string]string{
			"state": queryParams.Get("state"),
			"code":  queryParams.Get("code"),
		}).Get(callbackURL)
		if err != nil {
			ch <- err
			return
		}
		if resp.StatusCode() != 200 {
			ch <- fmt.Errorf("failed to get access token: %s", string(resp.Body()))
			return
		}
		color.Green("authorization success")
		_, _ = w.Write(resp.Body())
		ch <- nil
	}
}

var (
	githubAccessToken string
)

func authGitHubCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "auth github",
		Short: "authorize GitHub",
		Run: func(cmd *cobra.Command, args []string) {
			if githubAccessToken == "" {
				_ = cmd.Help()
				return
			}
			response, err := httpClient.R().SetBody(map[string]string{
				"access_token": githubAccessToken,
			}).Post("/auth/github")
			if err != nil {
				color.Red("failed to authorize GitHub: %v", err)
				os.Exit(-1)
			}
			if response.StatusCode() != 200 {
				color.Red("failed to authorize GitHub: %s", string(response.Body()))
				os.Exit(-1)
			}
			color.Green("authorization success")
		},
	}
	cmd.Flags().StringVar(&githubAccessToken, "access-token", "", "the access token for GitHub")

	return cmd
}
