import click
import os
import pkgutil
from dulwich import porcelain as git
from jinja2 import Template

import deploy
import context
import init
from objects import App


@click.group()
def cli():
    pass


@cli.command('deploy')
@click.argument('tag', required=False)
@click.option('--force', '-f', default=False, is_flag=True)
@context.required
def deploy_app(tag, force):
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


@cli.command('completion')
@click.pass_context
def get_completion(ctx):
    available_commands = cli.list_commands(ctx)
    raw_tpl = pkgutil.get_data('kyber', 'templates/kyber-completion.sh')
    click.echo(Template(raw_tpl).render(kyber_commands=available_commands))
