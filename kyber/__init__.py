import click
import os
import pkgutil
import sys
from dulwich import porcelain as git
from dulwich.errors import NotGitRepository
from jinja2 import Template

# logical modules
import dash
import deploy
import config
import context
import init
import shell
import status
import logs

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
@click.option('--yes', '-y', default=False, is_flag=True)
@context.required()
def deploy_app(ctx, tag, force, yes):
    """ trigger a deployment """

    ctx.set_git_hash(git_hash=tag)

    if not yes:
        status.echo(ctx)
        click.confirm("Continue?", abort=True, default=True)

    app = App(ctx.name, ctx.docker, ctx.tag)
    if not ecr.image_exists(app.image):
        click.echo("Can't find a docker for {}\naborting..".format(app.image))
        return

    click.echo("Deploying {}".format(ctx.tag))
    deployments = deploy.execute(app, force)
    deploy.wait_for(deployments)


@cli.command('init')
def init_app():
    """ create a new app, or sync with an existing one """
    cwd = os.path.abspath('.')

    try:
        repo = git.Repo.discover(cwd)
    except NotGitRepository:
        click.echo("No repository found")
        sys.exit(1)

    suggested_name = init.get_default_name(cwd)
    if suggested_name is None:
        click.echo("Unable to derive a name from the current git repository or directory!")
        sys.exit(2)

    name = click.prompt("Enter environment name".format(suggested_name), default=suggested_name)

    init.initialize(name, repo.head())


@cli.command('status')
@click.option('--skip-ecr', is_flag=True, default=False)
@click.option('--skip-k8s', is_flag=True, default=False)
@context.required()
def get_status(ctx, skip_ecr, skip_k8s):
    """ get the remote (k8s and ecr) status for the current kyber app context """
    status.echo(ctx, skip_ecr, skip_k8s)


@cli.command('logs')
@click.argument('pod', default=None, required=False)
@click.option('--since-seconds', '-s', default=3600, required=False)
@click.option('--keep-timestamps', '-k', default=False, required=False, is_flag=True)
@click.option('--follow', '-f', default=None, required=False, is_flag=True)
@context.required()
def get_logs(ctx, pod, since_seconds, keep_timestamps, follow):
    logs.get(ctx.name, pod, since_seconds, keep_timestamps, follow)


@cli.command('completion')
@click.pass_context
def get_completion(ctx):
    """ dump a bash/zsh compatible kb completion script """
    available_commands = cli.list_commands(ctx)
    available_config_commands = config_cli.list_commands(ctx)
    raw_tpl = pkgutil.get_data('kyber', 'templates/kyber-completion.sh')
    click.echo(Template(raw_tpl).render(
        kyber_commands=available_commands,
        kyber_config_commands=available_config_commands
    ))


@cli.command('shell')
@click.argument('shell_path', default='/bin/bash', required=False)
@context.required()
def run_shell(ctx, shell_path):
    """ execute a shell in the first possible pod (defaults to /bin/bash) """
    shell.run(ctx.name, shell_path)


@cli.command('dash')
def open_dashboard():
    """ Launch the kube-dashboard to see the pods running in the current kube context """
    dash.launch()


@cli.command('version')
def show_version():
    """ show the current kyber version """
    from kyber._version import __version__
    click.echo("Kyber version: {}".format(__version__))


@config_cli.command('list')
@context.required(checks=['config'])
def config_list(ctx):
    """ list configuration in var=value (envfile) format """
    env = Environment(ctx.name)
    cfg = env.secret
    for key in sorted(cfg.keys()):
        click.echo("{}={}".format(key, cfg[key]))


@config_cli.command('get')
@click.argument('key')
@context.required()
def config_get(ctx, key):
    """ get a single config variable """
    env = Environment(ctx.name)
    cfg = env.secret
    if key not in cfg:
        click.echo("No var found for `{}.{}`".format(context.name, key))
        return
    click.echo(cfg[key])


@config_cli.command('set')
@click.argument('key')
@click.argument('value')
@context.required()
def config_set(ctx, key, value):
    """ set a single config variable"""
    env = Environment(ctx.name)
    cfg = env.secret
    cfg[key] = value
    cfg.update()


@config_cli.command('unset')
@click.argument('key')
@context.required()
def config_unset(ctx, key):
    env = Environment(ctx.name)
    cfg = env.secret
    if click.confirm(u"Do you wish to delete config variable {}.{} with value of `{}`".format(
            ctx.name, key, cfg[key])):
        del cfg[key]
        cfg.update()


@config_cli.command('envdir')
@click.argument('target_dir')
@context.required()
def config_envdir(ctx, target_dir):
    env = Environment(ctx.name)
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
def config_load(ctx, source):
    source = os.path.abspath(source)
    env = Environment(ctx.name)

    if not os.path.exists(source):
        click.echo("Can't load vars from `{}` no such file or directory".format(source))
        sys.exit(1)

    if os.path.isdir(source):
        loaded_vars = config.read_envdir(source)

    if os.path.isfile(source):
        loaded_vars = config.read_envfile(source)

    if click.confirm("Found {} vars in `{}` do you wish to write them to {}".format(len(loaded_vars), source, env)):
        config.save_secret(env, loaded_vars)
