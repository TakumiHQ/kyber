""" kyber.deploy - logic and cli commands related to deploying a kyber project.
"""
import click
import json
import pykube
import time

from .objects import App, Deployment, Environment
from .lib.kube import kube_api


class DeploymentSpec(object):
    def __init__(self, deployment):
        self.spec = deployment.obj

    def update_image(self, app):
        self.spec['spec']['template']['spec']['containers'][0]['image'] = app.image

    def update_metadata(self, app):
        # labels must adhere to regex (([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])? (e.g. 'MyValue' or 'my_value'
        # or '12345') # so we use unix timestamp integer, instead of ios8601 string which contains ':' and '.'
        self.spec['spec']['template']['metadata']['labels']['deploy_time'] = str(int(time.time()))


def execute(app, force=False):
    environment = Environment(app.name)
    deployment = environment.deployment
    if not force and environment.app and environment.app.tag == app.tag:
        click.echo("`{}` is already deployed, use force to trigger redeployment".format(app.tag))
        return deployment

    update = DeploymentSpec(deployment)
    update.update_image(app)
    update.update_metadata(app)
    deployment.set_obj(update.spec)
    deployment.update()
    return deployment


def wait_for(deployment):
    old_generation = deployment.generation
    for event in Deployment.objects(kube_api).filter(namespace=kube_api.config.namespace).watch():
        depl = event.object
        if depl.name == deployment.name:
            click.echo(".", nl=False)
            if depl.ready is True:
                click.echo("\nDeployment complete, generation {} -> {}".format(old_generation, depl.generation))
                return
