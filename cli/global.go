package main

import (
	"encoding/json"
	"fmt"
	"io"
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
	npiCheckUpdateEndpoint = "https://check-cli.npi.ai/latest"
)

type CMDLatestVersion struct {
	Version string `json:"version"`
	URL     string `json:"url"`
}

func checkUpdate() error {
	cli := resty.New()
	cli.SetTimeout(1 * time.Second)
	f, err := os.OpenFile(filepath.Join(configHome, "last_check_update"), os.O_RDWR, 0664)
	if err != nil {
		if os.IsNotExist(err) {
			f, err = os.Create(filepath.Join(configHome, "last_check_update"))
		}
		if err != nil {
			return err
		}
	}
	data, err := io.ReadAll(f)
	if err != nil {
		return err
	}
	if string(data) != "" {
		t, err := time.Parse(time.RFC3339, string(data))
		if err == nil {
			if t.After(time.Now().Add(-10 * time.Second)) {
				return nil
			}
		}
	}
	response, err := resty.New().R().SetQueryParams(map[string]string{
		"version":        Version,
		"git_commit":     GitCommit,
		"platform":       Platform,
		"build_date":     BuildDate,
		"server_version": ServerVersion,
	}).Get(npiCheckUpdateEndpoint)
	if err != nil {
		return err
	}
	if response.StatusCode() != 200 {
		return fmt.Errorf("code: %d, reason: %s", response.StatusCode(), string(response.Body()))
	}
	latest := CMDLatestVersion{}
	_ = json.Unmarshal(response.Body(), &latest)
	if strings.Compare(Version, latest.Version) < 0 {
		color.Green("new version detected: %s, current version: %s. Download url: %s/%s", latest.Version, Version, latest.URL, Platform)
		// TODO download the latest version
	} else {
		_, _ = f.Seek(0, 0)
		_, err = f.Write([]byte(time.Now().Format(time.RFC3339)))
	}
	_ = f.Close()
	return nil
}

func checkConfig() {
	home, err := os.UserHomeDir()
	if err != nil {
		color.Red("failed to get home dir: %v ", err)
		os.Exit(-1)
	}
	configHome = filepath.Join(home, ".npiai")
	info, err := os.Stat(configHome)
	if err != nil {
		if os.IsNotExist(err) {
			err = os.Mkdir(configHome, 0755)
			if err != nil {
				color.Red("failed to create config home: %v ", err)
				os.Exit(-1)
			}
		} else {
			color.Red("failed to get config home: %v ", err)
			os.Exit(-1)
		}
	}
	if !info.IsDir() {
		color.Red("the config home is not a directory, please rm it and try again")
		os.Exit(-1)
	}
}

func readConfig() {
	f, err := os.Open(filepath.Join(configHome, configFileName))
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
	httpClient = resty.New().SetBaseURL("http://" + cfg.GetHTTPEndpoint())
	httpClient.SetHeader("Authorization", cfg.APIKey)
}
