import click

from objects import App, Environment
from lib import ecr


def echo(context, skip_k8s=False, skip_ecr=False):
    """ get the remote (k8s and ecr) status for the current kyber app context """
    app = App(context.name, context.docker, context.tag)

    click.echo("Project: {}".format(context.name))
    click.echo("Docker: {}".format(context.docker))
    if not skip_k8s:
        deployed_app = Environment(context.name).app
        click.echo("Deployed tag: {}".format(deployed_app.tag if deployed_app is not None else 'N/A'))

    deployable = '?'
    if not skip_ecr:
        deployable = 'y' if ecr.image_exists(app.image) else 'n'

    click.echo("Current tag: {} [deployable: {}]".format(context.tag, deployable))
    click.echo("Kubernetes target: {} ({})".format(context.kube_ctx['cluster'], context.kube_ctx['namespace']))
