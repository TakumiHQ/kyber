""" kyber.deploy - logic and cli commands related to deploying a kyber project.
"""
import click
import json
import pykube
import datetime as dt

from kyber.objects import App, Deployment
from kyber.lib.kube import kube_api


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
            # labels must adhere to regex (([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])? (e.g. 'MyValue' or 'my_value'
            # or '12345') # so we use unix timestamp integer, instead of is8601 string which contains ':' and '.'
            self.spec['spec']['template']['metadata']['labels']['deploy_time'] = int(time.time())


def execute(app, force=False):
    deployment = Deployment.objects(kube_api).get_or_none(name=app.name)

    update = DeploymentSpec(deployment)
    update.update_image(app)
    update.update_metadata(app, fresh_date=force)
    deployment.set_obj(update.spec)
    deployment.update()
    return deployment


def wait_for(deployment):
    old_generation = deployment.generation
    for event in Deployment.objects(kube_api).filter(namespace=config.namespace).watch():
        depl = event.object
        if depl.name == deployment.name:
            click.echo(depl.obj['status'])
            if depl.ready is True:
                click.echo("Deployment complete, generation {} -> {}".format(old_generation, depl.generation))
                return
