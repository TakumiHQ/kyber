import click
import os
import yaml

from dulwich import porcelain as git
from dulwich.errors import NotGitRepository

from kyber.objects import App, Environment
from kyber.lib.kube import kube_api


class InitError(Exception):
    pass


class Config(object):
    app = None
    _kyber_dir = os.path.join(os.path.abspath('.'), '.kyber')

    def __init__(self, app):
        self.app = app

    @classmethod
    def load_config(cls):
        config = {}
        filepath = os.path.join(cls._kyber_dir, 'config')
        if os.path.exists(filepath):
            with open(filepath) as config_file:
                config = yaml.load(config_file.read())
        return config

    @classmethod
    def from_file(cls, filepath, kube_ctx):
        config = cls.load_config()
        if kube_ctx not in config:
            return None
        context_cfg = config[kube_ctx]

        app = App(
            context_cfg['name'],
            context_cfg['docker'],
            context_cfg['tag'],
            context_cfg.get('port'),
            context_cfg.get('dns_name'),
            context_cfg.get('ssl_cert'),
        )
        return cls(app)

    def save(self, kube_ctx):
        if not os.path.exists(self._kyber_dir):
            os.mkdir(self._kyber_dir)
        config = self.load_config()
        with open(os.path.join(self._kyber_dir, 'config'), 'w') as cfg_file:
            config[kube_ctx] = self.app.to_dict()
            cfg_file.write(yaml.safe_dump(config, default_flow_style=False))


def get_default_name(cwd):
    """ Return a default name for a directory, based on repo name or directory name """

    try:
        repo = git.Repo(cwd)
    except NotGitRepository:
        repo = None

    if repo is not None:
        # Repo found, try to get repo name
        try:
            origin = repo.get_config()[('remote', 'origin')]['url']
            dotgit = origin.split('/')[-1]
            return dotgit.replace('.git', '')
        except (KeyError, IndexError):
            pass

    # Not a repo, return folder name
    try:
        return cwd.split('/')[-1]
    except:
        pass


def from_scratch(name, tag):
    docker = click.prompt(
        "Enter ECR (e.g. ...dkr.ecr.us-east-1.amazonaws.com/{})".format(name), default=os.environ.get('ECR'))
    port = click.prompt("Enter app port", default=5000)
    tag = click.prompt("Enter tag", default='git_{}'.format(tag))
    dns_name = click.prompt("Enter DNS name (enter for none)", default=None)
    ssl_cert = click.prompt("Enter SSL certificate ARN (enter for none)", default=None)
    app = App(name, docker, tag, port, dns_name, ssl_cert)
    return app


def initialize(name, tag):
    context = kube_api.config.current_context
    config = Config.from_file('.kyber/config', context)
    click.echo("Loading environment for {} from {}".format(name, kube_api.config.current_context))
    environment = Environment(name)

    if config is None:
        # no .kyber/config
        if environment.app is not None:
            click.echo("Found app in kubernetes environment")
            config = Config(environment.app)
            click.echo("App name: {}".format(config.app.name))
            click.echo("App docker: {}".format(config.app.docker))
            click.echo("App tag: {}".format(config.app.tag))
            if config.app.port:
                click.echo("App port: {}".format(config.app.port))
            if config.app.dns_name:
                click.echo("App DNS: {}".format(config.app.dns_name))
            if config.app.ssl_cert:
                click.echo("App SSL certificate: {}".format(config.app.ssl_cert))
        else:
            click.echo("No app found in kubernetes environment")
            app = from_scratch(name, tag)
            config = Config(app)
        if click.confirm("Save configuration to `.kyber/config`?"):
            config.save(context)

    environment.app = config.app
    if not environment.complete:
        click.echo("Environment for `{}` in `{}` is incomplete".format(name, context))
        environment.status()
        click.confirm("Create/update?", abort=True)
        environment.sync()
