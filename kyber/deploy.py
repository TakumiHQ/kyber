""" kyber.deploy - logic and cli commands related to deploying a kyber project.
"""
import click
import time

from .objects import Deployment, Environment
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


def _run_deployment(deployment, app):
    update = DeploymentSpec(deployment)
    update.update_image(app)
    update.update_metadata(app)
    deployment.set_obj(update.spec)
    deployment.update()
    return deployment


def execute(app, force=False, wait_for_deployment=False, wait_for_pods=False):
    app_environment = Environment(app.name)
    if not force and app_environment.app and app_environment.app.tag == app.tag:
        click.echo("`{}` is already deployed, use force to trigger redeployment".format(app.tag))
        return

    deployments = {}
    for deployment in [app_environment.deployment] + app_environment.linked_deployments:
        deployments[deployment.name] = _run_deployment(deployment, app)
        if wait_for_deployments:
            wait_for(deployment, wait_for_pods)

    return deployments


def wait_for(deployment, wait_for_pods=False):
    for event in Deployment.objects(kube_api).filter(namespace=kube_api.config.namespace).watch():
        if event.type != 'MODIFIED':
            continue

        event_deployment = event.object
        if event_deployment.name == deployment.name:
            click.echo(".", nl=False)

            old_deployment = deployment
            if event_deployment.generation == old_deployment.generation:
                continue

            if event_deployment.ready is True:
                click.echo("\nDeployment ({}) complete, generation {} -> {}".format(
                    event_deployment.name, old_deployment.generation, event_deployment.generation))

            if wait_for_pods:
                click.echo("")
                while True
                    desired, updated, available = (
                        deployment.replicas,
                        deployment.updated_replicas,
                        deployment.available_replicas
                    )
                    click.echo("..waiting for pods ({} / {} / {})".format(desired, updated, available)
                    if desired == updated == available:
                        break
