package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/fatih/color"
	"github.com/go-resty/resty/v2"
	"gopkg.in/yaml.v3"
)

var (
	cfg                    = CMDConfig{}
	configHome             string
	configFileName         = "config.yaml"
	httpClient             *resty.Client
	npiCheckUpdateEndpoint = "https://os.api.npi.ai/cli/lastest"
)

type CMDLatestVersion struct {
	Version  string            `json:"version"`
	Download map[string]string `json:"download"`
}

func checkUpdate() {
	cli := resty.New()
	cli.SetTimeout(1 * time.Second)
	response, err := resty.New().R().SetQueryParams(map[string]string{
		"version":        Version,
		"git_commit":     GitCommit,
		"platform":       Platform,
		"build_date":     BuildDate,
		"server_version": ServerVersion,
	}).Get(npiCheckUpdateEndpoint)
	if err != nil {
		color.Yellow("failed to check updating: %v ", err)
		return
	}
	if response.StatusCode() != 200 {
		color.Yellow("failed to check updating: %s ", string(response.Body()))
		return
	}
	latest := CMDLatestVersion{}
	_ = json.Unmarshal(response.Body(), &latest)
	if strings.Compare(Version, latest.Version) < 0 {
		//color.Green("the newer version detected, we're forcing update to latest version due to version is unstable ",
		//	latest.Version)
		color.Green("downloading from %s", latest.Version, latest.Download[Platform])
		// TODO
	}
}

func checkConfig() {
	home, err := os.UserHomeDir()
	if err != nil {
		color.Red("failed to get home dir: %v ", err)
		os.Exit(-1)
	}
	configHome = home
}

func readConfig() {
	f, err := os.Open(filepath.Join(configHome, ".npiai", configFileName))
	if err != nil {
		color.Red("the config file not found, please use 'npi connect' to connect to server")
		os.Exit(-1)
	}
	defer func() {
		_ = f.Close()
	}()
	decoder := yaml.NewDecoder(f)
	err = decoder.Decode(&cfg)
	if err != nil {
		color.Red("failed to read config file: %v ", err)
		os.Exit(-1)
	}
	httpClient = resty.New().SetBaseURL("http://" + cfg.NPIServer)
	httpClient.SetHeader("Authorization", cfg.APIKey)
}
