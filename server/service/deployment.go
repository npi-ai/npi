package service

import (
	"context"
	"encoding/base64"
	"errors"
	"fmt"

	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/log"
	"github.com/npi-ai/npi/server/model"
	k8serr "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	v1 "k8s.io/client-go/kubernetes/typed/apps/v1"
	"k8s.io/client-go/tools/clientcmd"
)

const (
	toolServingPort = 9140
)

type DeploymentService struct {
	clientSet        *kubernetes.Clientset
	deploymentClient v1.DeploymentInterface
	namespace        string
	client           dynamic.Interface
}

func NewDeploymentService(kubeConfig string, namespace string) *DeploymentService {
	// TODO use ServiceAccount
	config, err := clientcmd.BuildConfigFromFlags("", kubeConfig)
	if err != nil {
		panic(fmt.Sprintf("Failed to load kubeconfg: %v", err))
	}
	clientSet, err := kubernetes.NewForConfig(config)
	if err != nil {
		panic(fmt.Sprintf("Failed to create k8s client: %v", err))
	}

	client, err := dynamic.NewForConfig(config)
	if err != nil {
		panic(fmt.Errorf("error getting kubernetes config: %v\n", err))
	}

	return &DeploymentService{
		clientSet: clientSet,
		client:    client,
		namespace: namespace,
	}
}

const (
	secretFormat = "%s-env-secret"
)

func (cli *DeploymentService) CreateDeployment(ctx context.Context, name, image string,
	env []model.ToolEnv) error {
	if name == "" {
		return nil
	}
	secretName := fmt.Sprintf(secretFormat, name)
	data := map[string]string{}
	_env := make([]map[string]interface{}, 0)
	hasSecret := false
	for _, e := range env {
		if e.Secret {
			hasSecret = true
			_env = append(_env, map[string]interface{}{
				"name": e.Name,
				"valueFrom": map[string]interface{}{
					"secretKeyRef": map[string]interface{}{
						"name": secretName,
						"key":  e.Name,
					},
				},
			})
			data[e.Name] = base64.StdEncoding.EncodeToString([]byte(e.Value))
		} else {
			_env = append(_env, map[string]interface{}{
				"name":  e.Name,
				"value": e.Value,
			})
		}
	}
	if hasSecret {
		secretRes := schema.GroupVersionResource{
			Group:    "",
			Version:  "v1",
			Resource: "secrets",
		}
		secretObject := &unstructured.Unstructured{
			Object: map[string]interface{}{
				"apiVersion": "v1",
				"kind":       "Secret",
				"metadata": map[string]interface{}{
					"name": secretName,
				},
				"data": data,
			},
		}

		secret, err := cli.client.Resource(secretRes).Namespace(cli.namespace).
			Create(ctx, secretObject, metav1.CreateOptions{})
		if err != nil {
			log.Error(ctx).Str("name", name).Err(err).Msg("Failed to create secret")
			return api.ErrInternal.WithMessage("Failed to create secret")
		}
		log.Info(ctx).Str("name", secret.GetName()).Msg("success to create secret")
	}

	deploymentRes := schema.GroupVersionResource{
		Group:    "apps",
		Version:  "v1",
		Resource: "deployments",
	}

	// TODO(ISSUE #87) scale down to 0 when deployment failed to start
	deploymentObject := &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "apps/v1",
			"kind":       "Deployment",
			"metadata": map[string]interface{}{
				"name": name,
			},
			"spec": map[string]interface{}{
				"replicas": 1,
				"selector": map[string]interface{}{
					"matchLabels": map[string]interface{}{
						"app": name,
					},
				},
				"template": map[string]interface{}{
					"metadata": map[string]interface{}{
						"labels": map[string]interface{}{
							"app": name,
						},
					},
					"spec": map[string]interface{}{
						"containers": []map[string]interface{}{
							{
								"name":  name,
								"image": image,
								"ports": []map[string]interface{}{
									{
										"name":          "tool",
										"protocol":      "TCP",
										"containerPort": toolServingPort,
									},
								},
								"env": _env,
							},
						},
					},
				},
			},
		},
	}

	fmt.Println("Creating deployment using the unstructured object")
	deployment, err := cli.client.Resource(deploymentRes).Namespace(cli.namespace).
		Create(ctx, deploymentObject, metav1.CreateOptions{})
	if err != nil {
		log.Warn(ctx).Str("name", name).Err(err).Msg("Failed to create deployment")
		if hasSecret {
			if err = cli.deleteSecret(ctx, name); err != nil {
				log.Warn(ctx).Str("name", secretName).Err(err).Msg("Failed to delete secret")
			}
		}
		return api.ErrInternal.WithMessage("Failed to create deployment").WithError(err)
	}
	log.Info(ctx).Str("name", deployment.GetName()).Msg("Created deployment")
	return nil
}

func (cli *DeploymentService) deleteSecret(ctx context.Context, name string) error {
	if name == "" {
		return nil
	}
	secretRes := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "secrets",
	}

	secretObject := &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "v1",
			"kind":       "Secret",
			"metadata": map[string]interface{}{
				"name": name,
			},
		},
	}

	_, err := cli.client.Resource(secretRes).Namespace(cli.namespace).Get(ctx, secretObject.GetName(), metav1.GetOptions{})
	if err != nil {
		var k8sErr *k8serr.StatusError
		if errors.As(err, &k8sErr) && k8sErr.Status().Reason == metav1.StatusReasonNotFound {
			return nil
		}
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to get secret")
		return api.ErrInternal.WithMessage("Failed to get secret").WithError(err)
	}

	err = cli.client.Resource(secretRes).Namespace(cli.namespace).
		Delete(ctx, secretObject.GetName(), metav1.DeleteOptions{})
	if err != nil {
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to delete secret")
		return api.ErrInternal.WithMessage("Failed to delete secret").WithError(err)
	}
	log.Info(ctx).Str("name", secretObject.GetName()).Msg("Deleted secret")
	return nil
}

func (cli *DeploymentService) DeleteDeployment(ctx context.Context, name string) error {
	if name == "" {
		return nil
	}
	secretName := fmt.Sprintf(secretFormat, name)
	_ = cli.deleteSecret(ctx, secretName)
	deploymentRes := schema.GroupVersionResource{
		Group:    "apps",
		Version:  "v1",
		Resource: "deployments",
	}

	deploymentObject := &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "apps/v1",
			"kind":       "Deployment",
			"metadata": map[string]interface{}{
				"name": name,
			},
		},
	}

	_, err := cli.client.Resource(deploymentRes).Namespace(cli.namespace).Get(ctx, deploymentObject.GetName(), metav1.GetOptions{})
	if err != nil {
		var k8sErr *k8serr.StatusError
		if errors.As(err, &k8sErr) && k8sErr.Status().Reason == metav1.StatusReasonNotFound {
			return nil
		}
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to get deployment")
		return api.ErrInternal.WithMessage("Failed to get deployment").WithError(err)
	}

	err = cli.client.Resource(deploymentRes).Namespace(cli.namespace).
		Delete(ctx, deploymentObject.GetName(), metav1.DeleteOptions{})
	if err != nil {
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to delete deployment")
		return api.ErrInternal.WithMessage("Failed to delete deployment").WithError(err)
	}
	log.Info(ctx).Str("name", deploymentObject.GetName()).Msg("Deleted deployment")
	return nil
}

func (cli *DeploymentService) CreateService(ctx context.Context, name string) (string, error) {
	if name == "" {
		return "", nil
	}
	serviceRes := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "services",
	}

	serviceObject := &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "v1",
			"kind":       "Service",
			"metadata": map[string]interface{}{
				"name": name,
			},
			"spec": map[string]interface{}{
				"selector": map[string]interface{}{
					"app": name,
				},
				"ports": []map[string]interface{}{
					{
						"name":       "http",
						"protocol":   "TCP",
						"port":       toolServingPort,
						"targetPort": toolServingPort,
					},
				},
				"type": "ClusterIP",
			},
		},
	}

	service, err := cli.client.Resource(serviceRes).Namespace(cli.namespace).
		Create(ctx, serviceObject, metav1.CreateOptions{})
	if err != nil {
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to create service")
		return "", api.ErrInternal.WithMessage("Failed to create service").WithError(err)
	}
	log.Info(ctx).Str("name", service.GetName()).Msg("Created service")
	return fmt.Sprintf("%s.%s.svc.cluster.local:%d", name, cli.namespace, toolServingPort), nil
}

func (cli *DeploymentService) DeleteService(ctx context.Context, name string) error {
	if name == "" {
		return nil
	}
	serviceRes := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "services",
	}

	serviceObject := &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "v1",
			"kind":       "Service",
			"metadata": map[string]interface{}{
				"name": name,
			},
		},
	}

	_, err := cli.client.Resource(serviceRes).Namespace(cli.namespace).Get(ctx, serviceObject.GetName(), metav1.GetOptions{})
	if err != nil {
		var k8sErr *k8serr.StatusError
		if errors.As(err, &k8sErr) && k8sErr.Status().Reason == metav1.StatusReasonNotFound {
			return nil
		}
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to get service")
		return api.ErrInternal.WithMessage("Failed to get service").WithError(err)
	}

	err = cli.client.Resource(serviceRes).Namespace(cli.namespace).
		Delete(ctx, serviceObject.GetName(), metav1.DeleteOptions{})
	if err != nil {
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to delete service")
		return api.ErrInternal.WithMessage("Failed to delete service").WithError(err)
	}
	log.Info(ctx).Str("name", serviceObject.GetName()).Msg("Deleted service")
	return nil
}
