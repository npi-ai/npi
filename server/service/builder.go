package service

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

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

const (
	defaultSourceName = "source.zip"
)

type ToolDefine struct {
	Main         string             `yaml:"main"`
	Class        string             `yaml:"class"`
	Dependencies []model.Dependency `yaml:"dependencies"`
}

func (bs *BuilderService) build(ctx context.Context, md model.ToolMetadata) error {
	workDir := filepath.Join(bs.rootDir, utils.GenerateRandomString(12, false, false))
	if err := os.MkdirAll(workDir, os.ModePerm); err != nil {
		return api.ErrInternal.
			WithMessage(fmt.Sprintf("Failed to create work directory: %s", workDir)).WithError(err)
	}

	// 0. download source zip from S3
	sourceZipPath := filepath.Join(workDir, defaultSourceName)
	if err := bs.s3Service.DownloadObject(ctx, filepath.Join(md.ID, defaultSourceName),
		bs.s3Bucket, sourceZipPath); err != nil {
		return api.ErrInternal.
			WithMessage(fmt.Sprintf("Failed to download source zip from S3: %s", md.ID)).WithError(err)
	}
	targetDir := filepath.Join(workDir, "target")
	if err := utils.ExtractZip(sourceZipPath, targetDir); err != nil {
		return api.ErrInternal.
			WithMessage(fmt.Sprintf("Failed to extract source zip: %s", sourceZipPath)).WithError(err)
	}

	// 1. validate source code
	data, err := os.ReadFile(filepath.Join(targetDir, "npi.yml"))
	if err != nil {
		return api.ErrInternal.
			WithMessage("Failed to read tool.yml").WithError(err)
	}
	tool := ToolDefine{}
	if err = yaml.Unmarshal(data, &tool); err != nil {
		return api.ErrInternal.WithMessage("Failed to parse tool.yml").WithError(err)
	}

	if tool.Main == "" {
		return api.ErrInvalidRequest.WithMessage("main field is required in tool.yml")
	}

	if tool.Class == "" {
		return api.ErrInvalidRequest.WithMessage("class field is required in tool.yml")
	}

	err = utils.RunPython(bs.validateScript, map[string]string{
		"source":     filepath.Join(targetDir, tool.Main),
		"class_name": tool.Class,
	})
	if err != nil {
		return api.ErrInternal.WithMessage("Failed to validate source code").WithError(err)
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
		return api.ErrInternal.
			WithMessage("Failed to write pyproject.toml").WithError(err)
	}

	// 3. generate main.py
	entrypoint := fmt.Sprintf(entrypointTemplate, tool.Main, tool.Class)
	if err = os.WriteFile(filepath.Join(targetDir, "main.py"), []byte(entrypoint), os.ModePerm); err != nil {
		return api.ErrInternal.
			WithMessage("Failed to write main.py").WithError(err)
	}

	// 4. generate Dockerfile
	dockerfile := fmt.Sprintf(dockerfileTemplate)
	if err = os.WriteFile(filepath.Join(targetDir, "Dockerfile"), []byte(dockerfile), os.ModePerm); err != nil {
		return api.ErrInternal.
			WithMessage("Failed to write Dockerfile").WithError(err)
	}

	// 5. upload to S3
	cmd := exec.Command("tar", "-czvf", "target.tar.gz", "target")
	cmd.Dir = workDir
	if _, err = cmd.CombinedOutput(); err != nil {
		return api.ErrInternal.
			WithMessage("Failed to created target.tar.gz").WithError(err)
	}
	data, err = os.ReadFile(filepath.Join(workDir, "target.tar.gz"))
	if err != nil {
		return api.ErrInternal.
			WithMessage("Failed to read target.tar.gz").WithError(err)
	}
	if err = bs.s3Service.PutObject(ctx, filepath.Join(md.ID, "target.tar.gz"), bs.s3Bucket, data); err != nil {
		return api.ErrInternal.
			WithMessage("Failed to upload target.tar.gz to S3").WithError(err)
	}

	// 6. build docker image
	//cmd = f'docker buildx build --platform linux/amd64 -t {docker_registry}/cloud/tools:{md.id} . --push'
	cmd = exec.Command("docker", "buildx", "build", "--platform", "linux/amd64",
		"-t", fmt.Sprintf("%s/cloud/tools:%s", bs.dockerRegistry, md.ID), ".", "--push")
	cmd.Dir = targetDir
	if output, err := cmd.CombinedOutput(); err != nil {
		println(string(output))
		return api.ErrInternal.
			WithMessage("Failed to build docker image").WithError(err)
	}

	// 7. cleanup
	if err = os.RemoveAll(workDir); err != nil {
		log.Warn().Str("path", workDir).Msg("Failed to remove work directory")
	}
	return nil
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
import tokenize
import asyncio
import time

async def main():
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

    async with instance as i:
        # await i.wait() TODO add this method to BaseApp class
        time.sleep(1000)


if __name__ == '__main__':
    asyncio.run(main())
`

	dockerfileTemplate = `FROM npiai/python:3.12
COPY . /npiai/tools

SHELL ["/bin/bash", "-c"]

WORKDIR /npiai/tools
RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "/npiai/tools/main.py"]
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
)
