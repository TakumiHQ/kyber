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


def _run_deployment(environment_name, app, force=False):
    environment = Environment(environment_name)
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


def execute(app, force=False):

    main_deployment = _run_deployment(app.name, app, force=force)

    deployments = {
        main_deployment.name: main_deployment
    }

    # Check if there is a linked deployment
    linked_deployment = main_deployment.annotations.get('kyber.linked.deployment')
    if linked_deployment is not None:
        click.echo("Deploying linked deployment: {}".format(linked_deployment))

        side_deployment = _run_deployment(linked_deployment, app, force=True)
        deployments[side_deployment.name] = side_deployment

    return deployments


def wait_for(deployments):

    for event in Deployment.objects(kube_api).filter(namespace=kube_api.config.namespace).watch():
        depl = event.object
        if depl.name in deployments:
            click.echo(".", nl=False)

            if depl.ready is True:
                deployment = deployments.pop(depl.name)
                old_generation = deployment.generation

                click.echo("\nDeployment ({}) complete, generation {} -> {}".format(
                    depl.name, old_generation, depl.generation))
                if len(deployments) is 0:
                    return
