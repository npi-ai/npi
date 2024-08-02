package service

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"github.com/npi-ai/npi/server/utils"
	"gopkg.in/yaml.v3"
)

type BuilderService struct {
	dockerRegistry string
	s3Bucket       string
	s3Service      *db.S3
	rootDir        string
	validateScript string
}

func NewBuilderService(dockerRegistry, rootDir, validateScript string, config db.S3Config) *BuilderService {
	bs := &BuilderService{
		dockerRegistry: dockerRegistry,
		s3Bucket:       config.Bucket,
		s3Service:      db.GetAWSS3(config),
		rootDir:        rootDir,
		validateScript: validateScript,
	}
	return bs
}

const (
	defaultSourceName = "source.zip"
)

func (bs *BuilderService) Build(ctx context.Context, md model.ToolMetadata) (string, model.ToolDefine, error) {
	start := time.Now()
	workDir := filepath.Join(bs.rootDir, utils.GenerateRandomString(12, true, false, false))
	tool := model.ToolDefine{}

	if err := os.MkdirAll(workDir, os.ModePerm); err != nil {
		return "", tool, api.ErrInternal.
			WithMessage(fmt.Sprintf("Failed to create work directory: %s", workDir)).WithError(err)
	}

	// 0. download source zip from S3
	sourceZipPath := filepath.Join(workDir, defaultSourceName)
	if err := bs.s3Service.DownloadObject(ctx, filepath.Join(md.ID, defaultSourceName),
		bs.s3Bucket, sourceZipPath); err != nil {
		return "", tool, api.ErrInternal.
			WithMessage(fmt.Sprintf("Failed to download source zip from S3: %s", md.ID)).WithError(err)
	}
	targetDir := filepath.Join(workDir, "target")
	if err := utils.ExtractZip(sourceZipPath, targetDir); err != nil {
		return "", tool, api.ErrInternal.
			WithMessage(fmt.Sprintf("Failed to extract source zip: %s", sourceZipPath)).WithError(err)
	}

	// 1. validate source code
	data, err := os.ReadFile(filepath.Join(targetDir, "npi.yml"))
	if err != nil {
		if os.IsNotExist(err) {
			return "", tool, api.ErrInvalidRequest.WithMessage("npi.yml not found in root directory")
		}
		return "", tool, api.ErrInternal.
			WithMessage("Failed to read tool.yml").WithError(err)
	}
	if err = yaml.Unmarshal(data, &tool); err != nil {
		return "", tool, api.ErrInternal.WithMessage("Failed to parse tool.yml").WithError(err)
	}

	if tool.Main == "" {
		return "", tool, api.ErrInvalidRequest.WithMessage("main field is required in tool.yml")
	}

	if tool.Class == "" {
		return "", tool, api.ErrInvalidRequest.WithMessage("class field is required in tool.yml")
	}

	err = utils.RunPython(bs.validateScript, map[string]string{
		"source":     filepath.Join(targetDir, tool.Main),
		"class_name": tool.Class,
	})
	if err != nil {
		return "", tool, api.ErrInternal.WithMessage("Failed to validate source code").WithError(err)
	}

	mdStr := fmt.Sprintf("name = \"%s\"\n", md.Name)
	mdStr += fmt.Sprintf("version = \"%s\"\n", "1.0.0")
	mdStr += fmt.Sprintf("description = \"%s\"\n", "NPi Tools created by NPi Cloud")
	mdStr += fmt.Sprintf("authors = [\"%s\"]\n", strings.Join(md.Authors, `", "`))

	depStr := ""
	for _, v := range tool.Dependencies {
		depStr += fmt.Sprintf("%s = \"%s\"\n", v.Name, v.Version)
	}

	poetryToml := fmt.Sprintf(poetryTemplate, mdStr, depStr)
	if err = os.WriteFile(filepath.Join(targetDir, "pyproject.toml"), []byte(poetryToml), os.ModePerm); err != nil {
		return "", tool, api.ErrInternal.
			WithMessage("Failed to write pyproject.toml").WithError(err)
	}

	// 3. generate main.py
	entrypoint := fmt.Sprintf(entrypointTemplate, tool.Main, tool.Class, tool.Main, tool.Class)
	if err = os.WriteFile(filepath.Join(targetDir, "main.py"), []byte(entrypoint), os.ModePerm); err != nil {
		return "", tool, api.ErrInternal.
			WithMessage("Failed to write main.py").WithError(err)
	}

	// 4. generate Dockerfile
	dockerfile := fmt.Sprintf(dockerfileTemplate)
	if err = os.WriteFile(filepath.Join(targetDir, "Dockerfile"), []byte(dockerfile), os.ModePerm); err != nil {
		return "", tool, api.ErrInternal.
			WithMessage("Failed to write Dockerfile").WithError(err)
	}

	// 4. generate Dockerfile
	buildSpec := fmt.Sprintf(codebuildTemplate)
	if err = os.WriteFile(filepath.Join(targetDir, "buildspec.yml"), []byte(buildSpec), os.ModePerm); err != nil {
		return "", tool, api.ErrInternal.
			WithMessage("Failed to write Dockerfile").WithError(err)
	}

	// 5. upload to S3
	//cmd := exec.Command("zip", "-r", "target.zip", "target/")
	//cmd.Dir = workDir
	//if output, err := cmd.CombinedOutput(); err != nil {
	//	log.Warn().Str("output", string(output)).Msg("Failed to create target.zip")
	//	return "", tool, api.ErrInternal.
	//		WithMessage("Failed to created target.zip").WithError(err)
	//}

	if err = utils.ZipDir(filepath.Join(workDir, "target"), filepath.Join(workDir, "target.zip")); err != nil {
		log.Warn(ctx).Err(err).Msg("Failed to zip target directory")
		return "", tool, api.ErrInternal.WithMessage("Failed to zip target directory")
	}

	data, err = os.ReadFile(filepath.Join(workDir, "target.zip"))
	if err != nil {
		return "", tool, api.ErrInternal.
			WithMessage("Failed to read target.zip").WithError(err)
	}
	if err = bs.s3Service.PutObject(ctx, filepath.Join(md.ID, "target.zip"), bs.s3Bucket, data); err != nil {
		return "", tool, api.ErrInternal.
			WithMessage("Failed to upload target.zip to S3").WithError(err)
	}

	log.Info().Str("id", md.ID).
		Str("duration", time.Now().Sub(start).String()).
		Msg("target file has been uploaded to S3")

	// 6. cleanup
	if err = os.RemoveAll(workDir); err != nil {
		log.Warn().Str("path", workDir).Msg("Failed to remove work directory")
	}
	return filepath.Join(bs.s3Bucket, md.ID, "target.zip"), tool, nil
}

type ToolMetadata struct {
	ID          string
	Name        string
	Version     string
	Description string
	Authors     []string
}

var (
	entrypointTemplate = `import os
import sys
import importlib
import time
import asyncio
import json


def print_tool_spec():
    # Add the directory containing the file to sys.path
    module_dir, module_name = os.path.split('%s')
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)
    # Create an instance of the class
    tool_class = getattr(module, '%s')
    instance = tool_class()
    print(json.dumps(instance.export()))


def main():
    # Add the directory containing the file to sys.path
    module_dir, module_name = os.path.split('%s')
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)
    # Create an instance of the class
    tool_class = getattr(module, '%s')
    instance = tool_class()
    instance.server()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'spec':
            print_tool_spec()
        elif sys.argv[1] == 'server':
            print('Starting server...')
            main()
        else:
            print('Usage: python entrypoint.py spec|server')
            sys.exit(1)
    else:
        print('Usage: python entrypoint.py spec|server')
        sys.exit(1)

`

	dockerfileTemplate = `FROM 992297059634.dkr.ecr.us-west-2.amazonaws.com/python:3.12
COPY . /npiai/tools

SHELL ["/bin/bash", "-c"]

WORKDIR /npiai/tools
RUN poetry install
ENV NPIAI_SERVICE_MODE=true

ENTRYPOINT ["poetry", "run", "python", "main.py", "server"]
`

	poetryTemplate = `[tool.poetry]
package-mode = false
%s

[tool.poetry.dependencies]
%s

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
`

	codebuildTemplate = `version: 0.2
reports:
    toolspec:
      files:
        - "spec.yml"
      file-format: "YAML"
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
  build:
    commands:
      - echo Building the Docker image...
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
  post_build:
    commands:
      - echo Pushing the Docker image...
      - docker run --rm --entrypoint poetry $IMAGE_REPO_NAME:$IMAGE_TAG run python main.py spec > spec.yml
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
`
)
