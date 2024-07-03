package main

import (
	"github.com/fatih/color"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
	"log"
	"os"
	"path/filepath"
)

var (
	cfg            = CMDConfig{}
	configFileName = "config.yaml"
	configHome     string
)

func makeSureConfigFileExist() string {
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
			return filepath.Join(configHome, configFileName)
		} else {
			color.Red("failed to get config home: %v ", err)
			os.Exit(-1)
		}
	}
	if !info.IsDir() {
		color.Red("the config home is not a directory, please rm it and try again")
		os.Exit(-1)
	}
	return filepath.Join(configHome, configFileName)
}

func getGRPCConn() *grpc.ClientConn {
	var opts []grpc.DialOption
	if cfg.Insecure {
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
