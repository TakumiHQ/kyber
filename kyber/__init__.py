import click
import os
import pkgutil
from dulwich import porcelain as git
from jinja2 import Template

# logical modules
import deploy
import config
import context
import init
import shell

# objects and helpers
from objects import App, Environment
from lib import ecr


@click.group()
def cli():
    pass


@cli.group('config')
def config_cli():
    pass


@cli.command('deploy')
@click.argument('tag', required=False)
@click.option('--force', '-f', default=False, is_flag=True)
@context.required()
def deploy_app(tag, force):
    if tag is None:
        tag = context.tag
    if not tag.startswith('git_'):
        tag = 'git_{}'.format(tag)

    app = App(context.name, context.docker, tag)
    if not ecr.image_exists(app.image):
        click.echo("Can't find a docker for {}\naborting..".format(app.image))
        return

    click.echo("Deploying {}".format(tag))
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


@cli.command('status')
@click.option('--skip-ecr', is_flag=True, default=False)
@click.option('--skip-k8s', is_flag=True, default=False)
@context.required()
def get_status(skip_ecr, skip_k8s):
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


@cli.command('completion')
@click.pass_context
def get_completion(ctx):
    available_commands = cli.list_commands(ctx)
    available_config_commands = config_cli.list_commands(ctx)
    raw_tpl = pkgutil.get_data('kyber', 'templates/kyber-completion.sh')
    click.echo(Template(raw_tpl).render(
        kyber_commands=available_commands,
        kyber_config_commands=available_config_commands
    ))


@cli.command('shell')
@context.required()
def run_shell():
    shell.run(context.name)


@config_cli.command('list')
@context.required(checks=['config'])
def config_list():
    env = Environment(context.name)
    cfg = env.secret
    for key in sorted(cfg.keys()):
        click.echo("{}={}".format(key, cfg[key]))


@config_cli.command('get')
@click.argument('key')
@context.required()
def config_get(key):
    env = Environment(context.name)
    cfg = env.secret
    if not key in cfg:
        click.echo("No var found for `{}.{}`".format(context.name, key))
        return
    click.echo(cfg[key])


@config_cli.command('set')
@click.argument('key')
@click.argument('value')
@context.required()
def config_set(key, value):
    env = Environment(context.name)
    cfg = env.secret
    cfg[key] = value
    cfg.update()


@config_cli.command('unset')
@click.argument('key')
@context.required()
def config_unset(key):
    env = Environment(context.name)
    cfg = env.secret
    if click.confirm(u"Do you wish to delete config variable {}.{} with value of `{}`".format(
        context.name, key, cfg[key])):
        del cfg[key]
        cfg.update()


@config_cli.command('envdir')
@click.argument('target_dir')
@context.required()
def config_envdir(target_dir):
    env = Environment(context.name)
    cfg = env.secret
    target_dir = os.path.abspath(target_dir)
    if not click.confirm("found {} vars, will write to `{}/*`".format(len(cfg), target_dir)):
        click.echo("Exiting..")
        sys.exit(1)

    if not os.path.exists(target_dir):
        click.echo("{} did not exists, creating".format(target_dir))
        os.mkdir(target_dir)
    else:
        if os.path.exists(target_dir) and not os.path.isdir(target_dir):
            click.echo("{} exists but isn't a directory, unable to continue".format(target_dir))
            sys.exit(2)
    config.write_envdir(cfg, target_dir)


@config_cli.command('load')
@click.argument('source')
@context.required()
def config_load(source):
    source = os.path.abspath(source)
    env = Environment(context.name)

    if not os.path.exists(source):
        click.echo("Can't load vars from `{}` no such file or directory".format(source))
        sys.exit(1)

    if os.path.isdir(source):
        loaded_vars = config.read_envdir(source)

    if os.path.isfile(source):
        loaded_vars = config.read_envfile(source)

    if click.confirm("Found {} vars in `{}` do you wish to write them to {}".format(len(loaded_vars), source, env)):
        config.save_secret(env, loaded_vars)
