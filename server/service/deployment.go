package service

import (
	"context"
	"fmt"

	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/log"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	v1 "k8s.io/client-go/kubernetes/typed/apps/v1"
	"k8s.io/client-go/tools/clientcmd"
)

const (
	toolServingPort = 19140
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

func (cli *DeploymentService) CreateDeployment(ctx context.Context, name, image string,
	env []map[string]interface{}) error {
	deploymentRes := schema.GroupVersionResource{
		Group:    "apps",
		Version:  "v1",
		Resource: "deployments",
	}

	// TODO set restart policy
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
								"env": env,
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
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to create deployment")
		return api.ErrInternal.WithMessage("Failed to create deployment").WithError(err)
	}
	log.Info(ctx).Str("name", deployment.GetName()).Msg("Created deployment")
	return nil
}

func (cli *DeploymentService) DeleteDeployment(ctx context.Context, name string) error {
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

	err := cli.client.Resource(deploymentRes).Namespace(cli.namespace).
		Delete(ctx, deploymentObject.GetName(), metav1.DeleteOptions{})
	if err != nil {
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to delete deployment")
		return api.ErrInternal.WithMessage("Failed to delete deployment").WithError(err)
	}
	log.Info(ctx).Str("name", deploymentObject.GetName()).Msg("Deleted deployment")
	return nil
}

func (cli *DeploymentService) CreateService(ctx context.Context, name string) (string, error) {
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

	err := cli.client.Resource(serviceRes).Namespace(cli.namespace).
		Delete(ctx, serviceObject.GetName(), metav1.DeleteOptions{})
	if err != nil {
		log.Error(ctx).Str("name", name).Err(err).Msg("Failed to delete service")
		return api.ErrInternal.WithMessage("Failed to delete service").WithError(err)
	}
	log.Info(ctx).Str("name", serviceObject.GetName()).Msg("Deleted service")
	return nil
}
