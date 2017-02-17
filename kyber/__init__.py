import click
import deploy
import context


cli = click.group()

@cli.command('deploy')
@click.argument('target', required=False)
@click.argument('tag', required=False)
@context.required
def deploy(target=None, tag=None):
    if target is None:
        target = context.target
    if tag is None:
        tag = context.tag

    app = deploy.App(context.name, context.docker, tag)
    deploy.execute(app)
