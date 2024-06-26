package db

import (
	"bytes"
	"context"
	"fmt"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/npi-ai/npi/server/constant"
	"io"
	"os"
	"strings"
)

type S3 struct {
	cli *s3.Client
}

type S3Config struct {
	AccountID string `yaml:"account_id"` // only for R2
	Enable    bool   `yaml:"enable"`
	AK        string `yaml:"ak"`
	SK        string `yaml:"sk"`
	Region    string `yaml:"region"`
	Bucket    string `yaml:"bucket"`
	Endpoint  string `yaml:"endpoint"`
}

func GetCloudflareR2(cfg S3Config) *S3 {
	//https://fef624caaf39cd90f34029a5643c7d0f.r2.cloudflarestorage.com
	r2Resolver := aws.EndpointResolverWithOptionsFunc(func(service, region string, options ...interface{}) (aws.Endpoint, error) {
		return aws.Endpoint{
			SigningRegion: "auto",
			URL:           fmt.Sprintf("https://%s.r2.cloudflarestorage.com", cfg.AccountID),
		}, nil
	})

	dfCfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithEndpointResolverWithOptions(r2Resolver),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(cfg.AK, cfg.SK, "")),
		config.WithRegion("auto"),
	)
	if err != nil {
		panic(fmt.Sprintf("failed to init cloudflare r2: %s", err))
	}
	return &S3{cli: s3.NewFromConfig(dfCfg)}
}

func GetAWSS3(cfg S3Config) *S3 {
	s3Svc := &S3{}
	optFns := []func(*config.LoadOptions) error{
		config.WithRegion(cfg.Region),
	}
	if cfg.AK != "" && cfg.SK != "" {
		optFns = append(optFns, config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(cfg.AK, cfg.SK, "")))
	}
	s3Cfg, err := config.LoadDefaultConfig(context.TODO(), optFns...)
	if err != nil {
		panic(fmt.Sprintf("failed to init s3: %s", err))
	}

	s3Svc.cli = s3.NewFromConfig(s3Cfg)
	return s3Svc
}

func (s *S3) PutObject(ctx context.Context, key, bucket string, data []byte) error {
	_key := aws.String(strings.TrimLeft(key, constant.Slash))
	_, err := s.cli.PutObject(ctx, &s3.PutObjectInput{
		Bucket: &bucket,
		Key:    _key,
		Body:   bytes.NewReader(data),
	})

	return err
}

func (s *S3) GetObject(ctx context.Context, key, bucket string) ([]byte, error) {
	output, err := s.cli.GetObject(ctx, &s3.GetObjectInput{
		Key:    &key,
		Bucket: &bucket,
	})
	if err != nil {
		return nil, err
	}
	defer output.Body.Close()
	var buf bytes.Buffer
	_, err = buf.ReadFrom(output.Body)
	if err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

func (s *S3) DownloadObject(ctx context.Context, key, bucket, filename string) error {
	output, err := s.cli.GetObject(ctx, &s3.GetObjectInput{
		Key:    &key,
		Bucket: &bucket,
	})
	if err != nil {
		return err
	}
	data, err := io.ReadAll(output.Body)
	if err != nil {
		return err
	}
	if err = os.WriteFile(filename, data, 0644); err != nil {
		return err
	}
	return nil
}
