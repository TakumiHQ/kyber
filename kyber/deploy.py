""" kyber.deploy - logic and cli commands related to deploying a kyber project.
"""
import json
import pykube


class App(object):
    name = None
    docker = None
    tag = None
    def __init__(self, name, docker, tag):
        self.name = name
        self.docker = docker
        self.tag = tag

    @property
    def image(self):
        return "{}:{}".format(self.docker, self.tag)


class DeploymentSpec(object):
    def __init__(self, deployment):
        self.spec = deployment.obj

    def update_image(self, app):
        self.spec['spec']['template']['spec']['containers'][0]['image'] = app.image

    def update_metadata(self, app, fresh_date=False):
        self.spec['spec']['template']['metadata']['labels'] = dict(
            app=app.name,
            tag=app.tag,
        )
        if fresh_date:
            self.spec['spec']['metadata']['labels']['data'] = dt.datetime.now().isoformat()


def execute(app, force=False):
    config = pykube.KubeConfig.from_file("~/.kube/config")
    api = pykube.HTTPClient(config)
    deployment = pykube.Deployment.objects(api).get_or_none(name=app.name)

    update = DeploymentSpec(deployment)
    update.update_image(app)
    update.update_metadata(app, fresh_date=force)
    deployment.set_obj(update.spec)
    deployment.update()
