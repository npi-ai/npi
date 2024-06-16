package reconcile

import (
	"context"
	"encoding/json"
	"errors"
	"github.com/mattn/go-isatty"
	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/db"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	"github.com/npi-ai/npi/server/service"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"os"
	"os/exec"
	"strings"
	"time"
)

// state transition:
//
// draft -> queued -> deploying -> running -> delete_marked -> deleting -> deleted
// running -> pause_marked -> pausing -> paused
// deploying/running/deleting/pausing -> error
type toolReconciler struct {
	BaseReconciler[model.ToolInstance]
	coll       *mongo.Collection
	builderSvc *service.BuilderService
}

func NewToolReconciler() Reconciler[model.ToolInstance] {
	return &toolReconciler{
		coll: db.GetCollection(db.CollToolInstances),
		builderSvc: service.NewBuilderService(
			"992297059634.dkr.ecr.us-west-2.amazonaws.com",
			"npiai-tools-build-test",
			"/Users/wenfeng/tmp/build",
			"/Users/wenfeng/workspace/npi-ai/npi/server/scripts/tool_helper.py",
		),
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

func (tc *toolReconciler) BuildingHandler(ctx context.Context, toolInstance model.ToolInstance) error {
	imageURI, err := tc.builderSvc.Build(ctx, toolInstance.Metadata)
	if err != nil {
		return err
	}

	args := []string{"run", "--rm", "--entrypoint", "poetry", imageURI, "run", "python", "main.py", "spec"}
	// get tool spec
	if isatty.IsTerminal(os.Stdin.Fd()) {
		//args = append([]string{"-it"}, args...)
	}
	cmd := exec.Command("docker", args...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		log.Warn().Str("output", string(output)).Msg("Failed to build docker image")
		return api.ErrInternal.
			WithMessage("Failed to build docker image").WithError(err)
	}

	strings.Split(string(output), "\n")
	success := false
	var md model.ToolMetadata
	var spec model.ToolFunctionSpec
	for _, line := range strings.Split(string(output), "\n") {
		if strings.HasPrefix(line, "{\"kind\"") {
			md, spec, err = parseToolSpec([]byte(line))
			if err != nil {
				return api.ErrInternal.
					WithMessage("Failed to parse tool spec").WithError(err)
			}

			success = true
			break
		}
	}
	if !success {
		return api.ErrInternal.WithMessage("Failed to get tool spec")
	}

	toolInstance.Metadata.Name = md.Name
	toolInstance.Metadata.Description = md.Description
	toolInstance.FunctionSpec = spec
	// upload image
	log.Info().Str("image", imageURI).Msg("Uploading docker image")
	cmd = exec.Command("docker", "push", imageURI)
	if output, err = cmd.CombinedOutput(); err != nil {
		log.Warn().Str("output", string(output)).Msg("Failed to upload docker image")
		return api.ErrInternal.
			WithMessage("Failed to upload docker image").WithError(err)
	}
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

func (tc *toolReconciler) DeployingHandler(ctx context.Context, ws model.ToolInstance) error {
	println("deploying")
	return nil
}

func (tc *toolReconciler) DeletingHandler(ctx context.Context, ws model.ToolInstance) error {
	println("deleting")
	return nil
}

func (tc *toolReconciler) PausingHandler(ctx context.Context, ws model.ToolInstance) error {
	println("pausing")
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
