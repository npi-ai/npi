package main

import (
	"encoding/json"
	"github.com/fatih/color"
	"github.com/pkg/browser"
	"github.com/spf13/cobra"
	"io"
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
			m := map[string]string{}
			_ = json.Unmarshal(response.Body(), &m)
			err = browser.OpenURL(m["url"])
			// TODO start a local server to receive the callback
			// then forward request to the server
		},
	}
	cmd.Flags().StringVar(&googleSecretFile, "secret-file", "", "the secret file for Google API")
	return cmd
}

func authGitHubCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "auth github",
		Short: "authorize GitHub",
	}

	return cmd
}
