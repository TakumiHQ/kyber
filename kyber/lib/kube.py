import pykube

config = pykube.KubeConfig.from_file("~/.kube/config")
kube_api = pykube.HTTPClient(config)
