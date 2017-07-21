import click
import os
import time

from objects import App, Environment
from lib import ecr
from dulwich import porcelain as git


def echo(context, skip_k8s=False, skip_ecr=False):
    """ get the remote (k8s and ecr) status for the current kyber app context """
    app = App(context.name, context.docker, context.tag)
    cwd = os.path.abspath('.')
    repo = git.Repo.discover(cwd)

    environment = Environment(app.name)

    click.echo("Project: {}".format(context.name))
    for linked_deployment in environment.linked_deployments:
        click.echo("Linked deployment: {}".format(linked_deployment.name))
    click.echo("Kubernetes target: {} ({})".format(context.kube_ctx['cluster'], context.kube_ctx['namespace']))
    click.echo("Docker registry: {}".format(context.docker))
    if not skip_k8s:
        deployed_app = Environment(context.name).app
        click.echo("Deployed tag: {}".format(deployed_app.tag if deployed_app is not None else 'N/A'))

    deployable = '?'
    if not skip_ecr:
        deployable = 'y' if ecr.image_exists(app.image) else 'n'

    click.echo("Current tag: {} [deployable: {}]".format(context.tag, deployable))

    try:
        commit = repo.get_object(context.git_hash)

        # Indent the whole message to make it stand out more in the status output
        indent = 4
        indented_message = ''.join(' ' * indent + line for line in commit.message.splitlines(True))

        click.echo("")
        click.echo("Author: {}".format(commit.author))
        click.echo("Date:   {}".format(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(commit.commit_time))))
        click.echo("")
        click.echo("{}".format(indented_message))
    except KeyError:
        click.echo("Commit not found in local repository")
