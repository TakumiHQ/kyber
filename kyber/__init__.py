import click

import deploy
import context
import init
from objects import App


@click.group()
def cli():
    pass


@cli.command('deploy')
@click.argument('target', required=False)
@click.argument('tag', required=False)
@context.required
def deploy_app(target=None, tag=None):
    if target is None:
        target = context.target
    if tag is None:
        tag = context.tag
    if not tag.startswith('git_'):
        tag = 'git_{}'.format(tag)

    print "Deploying {}".format(tag)
    app = App(context.name, context.docker, tag)
    deployment = deploy.execute(app)
    deploy.wait_for(deployment)


@cli.command('init')
def init_app():
    init.initialize()
