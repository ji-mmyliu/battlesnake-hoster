import kubernetes
import uuid
import logging
import time
import requests

from django.conf import settings
# from ..models import Snake, HostedSnake

logger = logging.getLogger(__name__)
server_cluster = settings.SERVER_CLUSTER

# Connect to Battlesnake kubernetes host cluster
logger.info(f'attempting to connect to host cluster...')
client = kubernetes.dynamic.DynamicClient(
    kubernetes.client.api_client.ApiClient(
        configuration=kubernetes.config.load_kube_config())
)
logger.info('connected to host cluster!')


class HostedSnake:
    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url


def update_source_code(snake, filename: str):
    files = {'new_src': open(filename, 'rb')}
    r = requests.post(f"{snake.snake_url}refresh", files=files)


def create_battlesnake_server(snake, wait=True):
    unique_identifier = snake.uuid.hex[-7:]

    job_v1 = client.resources.get(
        api_version="batch/v1", kind="Job")
    service_v1 = client.resources.get(api_version="v1", kind="Service")
    ingress_v1 = client.resources.get(
        api_version="networking.k8s.io/v1", kind="Ingress")

    hosted_snake_id = unique_identifier
    hosted_snake_name = f"{snake.name.lower()}-{hosted_snake_id}"
    hosted_snake_url = server_cluster["domain"].format(hosted_snake_name)

    labels = {
        "snake-name": hosted_snake_name,
        "snake-owner": snake.owner.username,
        "snake-id": hosted_snake_id,
        "app.kubernetes.io/component": "snake",
        "app.kubernetes.io/managed-by": "battlesnakehoster",
    }

    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": hosted_snake_name,
            "labels": labels,
        },
        "spec": {
            "backoffLimit": 4,
            "ttlSecondsAfterFinished": 0,
            "template": {
                "metadata": {
                    "labels": labels,
                    "annotations": {},
                },
                "spec": {
                    "containers": [
                        {
                            "name": "battlesnake-java-server",
                            "image": "ghcr.io/ji-mmyliu/starter-snake-java:latest"
                        }
                    ],
                    "restartPolicy": "OnFailure",
                },
            },
        },
    }

    job = job_v1.create(body=job_manifest,
                        namespace=server_cluster["namespace"])

    service_manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f'{hosted_snake_name}-expose-http',
            "labels": labels,
            "ownerReferences": [
                {
                    "apiVersion": "batch/v1",
                    "kind": "Job",
                    "name": job.metadata.name,
                    "uid": job.metadata.uid,
                }
            ],
        },
        "spec": {
            "type": "ClusterIP",
            "selector": {
                "snake-id": hosted_snake_id,
            },
            "ports": [
                {
                    "name": "expose-http",
                    "protocol": "TCP",
                    "port": 8000,
                    "targetPort": 8000,
                }
            ],
        },
    }

    clusterip_svc = service_v1.create(
        body=service_manifest, namespace=server_cluster["namespace"])

    ingress_manifest = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": hosted_snake_name,
            "labels": labels,
            "ownerReferences": [
                {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "name": clusterip_svc.metadata.name,
                    "uid": clusterip_svc.metadata.uid,
                }
            ],
            "annotations": {
                "kubernetes.io/ingress.class": "nginx"
            }
        },
        "spec": {
            "rules": [
                {
                    "host": hosted_snake_url,
                    "http": {
                        "paths": [
                            {
                                "pathType": "Prefix",
                                "path": "/",
                                "backend": {
                                    "service": {
                                        "name": clusterip_svc.metadata.name,
                                        "port": {
                                            "number": 8000,
                                        },
                                    },
                                },
                            }
                        ],
                    },
                }
            ],
        },
    }

    ingress = ingress_v1.create(
        body=ingress_manifest, namespace=server_cluster["namespace"])

    if wait:
        pod_v1 = client.resources.get(api_version="v1", kind="Pod")
        while True:
            time.sleep(1)
            pod_list = pod_v1.get(
                namespace=server_cluster["namespace"],
                label_selector=f"snake-owner={snake.owner.username},snake-id={unique_identifier}",
            ).items

            if len(pod_list) > 0 and pod_list[0] and pod_list[0]["status"]["phase"] != "Pending":
                break

    return fetch_battlesnake_server(snake)


def fetch_battlesnake_server(snake):
    unique_identifier = snake.uuid.hex[-7:]

    job_v1 = client.resources.get(api_version="batch/v1", kind="Job")

    job_list = job_v1.get(
        namespace=server_cluster["namespace"],
        label_selector=f"snake-owner={snake.owner.username},snake-id={unique_identifier}",
    )

    if len(job_list.items) == 0:
        return None

    job = job_list.items[0]

    hosted_snake_id = unique_identifier
    hosted_snake_name = job.metadata.name
    hosted_snake_url = server_cluster["domain"].format(hosted_snake_name)

    return HostedSnake(id=hosted_snake_id, name=job.metadata.name, url=f"http://{hosted_snake_url}/")


def delete_battlesnake_server(snake):
    job_v1 = client.resources.get(api_version="batch/v1", kind="Job")

    unique_identifier = snake.uuid.hex[-7:]

    existing_battlesnake_server = fetch_battlesnake_server(snake)

    if not existing_battlesnake_server:
        return

    job_v1.delete(
        namespace=server_cluster["namespace"],
        name=existing_battlesnake_server.name,
        propagation_policy="Background",
    )
