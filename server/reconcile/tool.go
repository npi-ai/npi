package reconcile

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/codebuild"
	"github.com/aws/aws-sdk-go-v2/service/codebuild/types"
	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"github.com/npi-ai/npi/server/service"
	"github.com/npi-ai/npi/server/utils"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"time"
)

// state transition:
//
// draft -> queued -> deploying -> running -> delete_marked -> deleting -> deleted
// running -> pause_marked -> pausing -> paused
// deploying/running/deleting/pausing -> error
type toolReconciler struct {
	BaseReconciler[model.ToolInstance]
	coll            *mongo.Collection
	builderSvc      *service.BuilderService
	deploySvc       *service.DeploymentService
	codeBuildClient *codebuild.Client
	cfg             ToolReconcilerConfig
	buildCfg        ImageBuildConfig
	s3Cli           *db.S3
}

type ImageBuildConfig struct {
	Project   string `yaml:"project"`
	Region    string `yaml:"region"`
	AccountID string `yaml:"account_id"`
	ImageRepo string `yaml:"image_repo"`
}

type ToolReconcilerConfig struct {
	DockerRegistry   string           `yaml:"docker_registry"`
	S3Bucket         string           `yaml:"bucket"`
	Workdir          string           `yaml:"workdir"`
	ValidateScript   string           `yaml:"validate_script"`
	KubeConfig       string           `yaml:"kubeconfig"`
	Namespace        string           `yaml:"namespace"`
	AccessEndpoint   string           `yaml:"access_endpoint"`
	ImageBuildConfig ImageBuildConfig `yaml:"build"`
}

func NewToolReconciler(cfg ToolReconcilerConfig) Reconciler[model.ToolInstance] {
	optFns := []func(*config.LoadOptions) error{
		config.WithRegion(cfg.ImageBuildConfig.Region),
	}
	//if cfg.AK != "" && cfg.SK != "" {
	//	optFns = append(optFns, config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(cfg.AK, cfg.SK, "")))
	//}
	cbCfg, err := config.LoadDefaultConfig(context.TODO(), optFns...)
	if err != nil {
		panic(fmt.Sprintf("failed to init s3: %s", err))
	}
	c3cfg := db.S3Config{
		Bucket: cfg.S3Bucket,
	}
	return &toolReconciler{
		coll: db.GetCollection(db.CollToolInstances),
		builderSvc: service.NewBuilderService(
			cfg.DockerRegistry,
			cfg.Workdir,
			cfg.ValidateScript,
			c3cfg,
		),
		s3Cli:           db.GetAWSS3(c3cfg),
		codeBuildClient: codebuild.NewFromConfig(cbCfg),
		deploySvc:       service.NewDeploymentService(cfg.KubeConfig, cfg.Namespace),
		cfg:             cfg,
		buildCfg:        cfg.ImageBuildConfig,
	}
}

func (tc *toolReconciler) Start(ctx context.Context) error {
	tc.BaseReconciler.SetName("Tool")
	g := func() model.ToolInstance {
		return model.ToolInstance{}
	}

	// recover tools in progress
	result, err := tc.coll.UpdateMany(ctx,
		bson.M{
			"in_progress": true,
		},
		[]bson.M{
			{"$set": bson.M{
				"current_state": "$source_state",
				"in_progress":   false,
			}},
		})
	if err != nil {
		return db.ConvertError(err)
	}
	log.Info().Int("recovered", int(result.ModifiedCount)).Msg("tool recovered")
	go tc.Reconcile(ctx, tc.coll,
		model.ResourceStatusCreated,
		model.ResourceStatusBuilding,
		model.ResourceStatusBuilt,
		g, tc.BuildingHandler)

	go tc.Reconcile(ctx, tc.coll,
		model.ResourceStatusQueued,
		model.ResourceStatusDeploying,
		model.ResourceStatusRunning,
		g, tc.DeployingHandler)

	go tc.Reconcile(ctx, tc.coll,
		model.ResourceStatusDeleteMarked,
		model.ResourceStatusDeleting,
		model.ResourceStatusDeleted,
		g, tc.DeletingHandler)

	go tc.Reconcile(ctx, tc.coll,
		model.ResourceStatusPauseMarked,
		model.ResourceStatusPausing,
		model.ResourceStatusPaused,
		g, tc.PausingHandler)
	return nil
}

var (
	regionKey        = "AWS_DEFAULT_REGION"
	accountIDKey     = "AWS_ACCOUNT_ID"
	imageTagKey      = "IMAGE_TAG"
	imageRepoNameKey = "IMAGE_REPO_NAME"
)

func (tc *toolReconciler) buildImage(ctx context.Context, imageRepo, imageTag, s3Path string) (string, error) {
	// build docker image
	buildOutput, err := tc.codeBuildClient.StartBuild(ctx, &codebuild.StartBuildInput{
		ProjectName:            &tc.buildCfg.Project,
		SourceLocationOverride: &s3Path,
		EnvironmentVariablesOverride: []types.EnvironmentVariable{
			{
				Name:  &regionKey,
				Value: &tc.buildCfg.Region,
			},
			{
				Name:  &accountIDKey,
				Value: &tc.buildCfg.AccountID,
			},
			{
				Name:  &imageRepoNameKey,
				Value: &imageRepo,
			},
			{
				Name:  &imageTagKey,
				Value: &imageTag,
			},
		},
	})
	if err != nil {
		log.Warn().Err(err).Msg("Failed to start codebuild")
		return "", api.ErrInternal.WithMessage("Failed to build docker image")
	}
	for {
		output, err := tc.codeBuildClient.BatchGetBuilds(ctx, &codebuild.BatchGetBuildsInput{
			Ids: []string{*buildOutput.Build.Id},
		})
		if err != nil {
			log.Warn().Err(err).Msg("Failed to get build output")
			return "", api.ErrInternal.WithMessage("Failed to build docker image")
		}
		switch output.Builds[0].BuildStatus {
		case types.StatusTypeSucceeded:
			arn := strings.Split(output.Builds[0].ReportArns[0], "/")
			if len(arn) != 2 {
				return "", api.ErrInternal.WithMessage("error at get tool spec")
			}
			return arn[1], nil
		case types.StatusTypeInProgress:
			time.Sleep(5 * time.Second)
			continue
		default:
			log.Warn().Interface("status", output.Builds[0].BuildStatus).Msg("Failed to build docker image")
			return "", api.ErrInternal.WithMessage("Failed to build docker image")
		}
	}
}

var (
	buildReportPath = "toolspec/%s/TEST/%s-%s/npiai-test-tool-build-toolspec-raw/spec.yml"
)

func (tc *toolReconciler) BuildingHandler(ctx context.Context, toolInstance model.ToolInstance) error {
	s3Path, tool, err := tc.builderSvc.Build(ctx, toolInstance.Metadata)
	if err != nil {
		return err
	}

	buildReportID, err := tc.buildImage(ctx, tc.buildCfg.ImageRepo, toolInstance.ID.Hex(), s3Path)
	if err != nil {
		return err
	}

	strs := strings.Split(buildReportID, ":")
	if len(strs) != 2 {
		return api.ErrInternal.WithMessage("error at get tool spec")
	}
	toolGroup := strs[0]
	reportID := strs[1]
	specS3Path := fmt.Sprintf(buildReportPath, toolGroup, toolGroup, reportID)
	data, err := tc.s3Cli.GetObject(ctx, fmt.Sprintf(buildReportPath, toolGroup, toolGroup, reportID), tc.cfg.S3Bucket)
	if err != nil {
		log.Warn(ctx).
			Str("id", toolInstance.ID.Hex()).
			Str("spec_path", specS3Path).
			Err(err).Msg("failed to parse tool")
		return api.ErrInternal.WithMessage("failed to parse tool spec")
	}

	md, spec, err := parseToolSpec(data)
	if err != nil {
		return api.ErrInternal.
			WithMessage("Failed to parse tool spec").WithError(err)
	}

	log.Info().Str("id", md.ID).Msg("Tool spec has been parsed successfully")

	imageURI := fmt.Sprintf("%s/%s:%s", tc.cfg.DockerRegistry, tc.buildCfg.ImageRepo, toolInstance.ID.Hex())
	toolInstance.Metadata.Name = md.Name
	toolInstance.Metadata.Description = md.Description
	spec.Env = tool.Environment
	toolInstance.FunctionSpec = spec

	// update tool instance
	_, err = tc.coll.UpdateOne(ctx,
		bson.M{"_id": toolInstance.ID},
		bson.M{
			"$set": bson.M{
				"metadata":   toolInstance.Metadata,
				"spec":       toolInstance.FunctionSpec,
				"image":      imageURI,
				"updated_at": time.Now(),
			},
		})
	return db.ConvertError(err)
}

func (tc *toolReconciler) DeployingHandler(ctx context.Context, toolInstance model.ToolInstance) error {
	name := utils.GenerateRandomString(12, false, false, false)
	if err := tc.deploySvc.CreateDeployment(ctx, name, toolInstance.Image, toolInstance.FunctionSpec.Env); err != nil {
		return err
	}
	rollbackDeployment := func() {
		if err := tc.deploySvc.DeleteDeployment(ctx, name); err != nil {
			log.Warn().
				Str("id", toolInstance.Metadata.ID).
				Str("name", name).
				Err(err).Msg("Failed to rollback deployment")
		}
	}
	svcUrl, err := tc.deploySvc.CreateService(ctx, name)
	if err != nil {
		rollbackDeployment()
		return err
	}
	rollbackService := func() {
		if _err := tc.deploySvc.DeleteService(ctx, name); _err != nil {
			log.Warn().
				Str("id", toolInstance.Metadata.ID).
				Str("name", name).
				Err(_err).Msg("Failed to rollback service")
		}
	}
	_, err = tc.coll.UpdateOne(ctx,
		bson.M{"_id": toolInstance.ID},
		bson.M{
			"$set": bson.M{
				"service_url": svcUrl,
				"deploy_name": name,
				"updated_at":  time.Now(),
			},
		})

	if err != nil {
		rollbackDeployment()
		rollbackService()
		return db.ConvertError(err)
	}

	return nil
}

func (tc *toolReconciler) DeletingHandler(ctx context.Context, toolInstance model.ToolInstance) error {
	if err := tc.deploySvc.DeleteDeployment(ctx, toolInstance.DeployName); err != nil {
		return err
	}

	if err := tc.deploySvc.DeleteService(ctx, toolInstance.DeployName); err != nil {
		return err
	}
	return nil
}

func (tc *toolReconciler) PausingHandler(ctx context.Context, toolInstance model.ToolInstance) error {
	// scale down deployment
	return nil
}

func parseToolSpec(data []byte) (model.ToolMetadata, model.ToolFunctionSpec, error) {
	m := map[string]interface{}{}
	md := model.ToolMetadata{}
	spec := model.ToolFunctionSpec{}
	if err := json.Unmarshal(data, &m); err != nil {
		return md, spec, err
	}
	if v, ok := m["metadata"]; ok {
		mdMap := v.(map[string]interface{})
		value, exist := mdMap["name"]
		if !exist {
			return md, spec, errors.New("metadata.name not found")
		}
		md.Name = value.(string)

		value, exist = mdMap["description"]
		if !exist {
			return md, spec, errors.New("metadata.description not found")
		}
		md.Description = value.(string)
	}
	if v, ok := m["spec"]; ok {
		d, err := json.Marshal(v)
		if err != nil {
			return md, spec, errors.New("failed to parse function spec")
		}
		if err = json.Unmarshal(d, &spec); err != nil {
			return md, spec, err
		}
		// TODO merge dependencies
	}
	return md, spec, nil
}
