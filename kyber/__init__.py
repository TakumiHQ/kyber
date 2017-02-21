import click
import os
from dulwich import porcelain as git

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
@click.option('--force', '-f', default=False, is_flag=True)
@context.required
def deploy_app(target, tag, force):
    if target is None:
        target = context.target
    if tag is None:
        tag = context.tag
    if not tag.startswith('git_'):
        tag = 'git_{}'.format(tag)

    print "Deploying {}".format(tag)
    app = App(context.name, context.docker, tag)
    deployment = deploy.execute(app, force)
    deploy.wait_for(deployment)


@cli.command('init')
def init_app():
    cwd = os.path.abspath('.')
    repo = git.Repo(cwd)
    name = init.get_default_name(repo)
    if name is None:
        click.prompt("Unable to derive a name from the current git repository or directory!")
        sys.exit(1)
    init.initialize(name, repo)
