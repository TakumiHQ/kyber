import click
import os
import sys
import yaml
from dulwich import porcelain as git
from jinja2 import Template
from pykube.objects import Service

from kyber.objects import App, Deployment
from kyber.lib.kube import kube_api


class InitError(Exception):
    pass


class ContextNotFound(Exception):
    pass


class Config(object):
    app = None
    _kyber_dir = os.path.join(os.path.abspath('.'), '.kyber')

    def __init__(self, app):
        self.app = app

    @classmethod
    def from_kubernetes(cls, deployment, service):
        """ Create an App object by finding the relevant data in kubernetes
        Deployment, Service (and later Secrets) objects.
        """
        metadata = deployment.obj['spec']['template']['metadata']
        spec = deployment.obj['spec']['template']['spec']

        name = metadata['labels']['app']
        tag = metadata['labels']['tag']
        docker = spec['containers'][0]['image'].split(":")[0]
        port = spec['containers'][0]['ports'][0].get('containerPort')
        app = App(name, docker, tag, port)

        if service is not None:
            metadata = service.obj['metadata']
            if 'dns' in metadata['labels']:
                dns_name = metadata['annotations']['domainName']
                app.dns_name = dns_name
            if 'service.beta.kubernetes.io/aws-load-balancer-ssl-cert' in metadata['annotations']:
                app.ssl_cert = metadata['annotations']['service.beta.kubernetes.io/aws-load-balancer-ssl-cert']

        return cls(app)

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
            raise ContextNotFound()
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
        config = cls.load_config
        with open(os.path.join(self._kyber_dir, 'config'), 'w') as cfg_file:
            config[kube_ctx] = self.app.to_dict()
            cfg_file.write(yaml.safe_dump(config, default_flow_style=False))


def get_default_name(repo):
    # 1. try to find name from remote origin (ie. git@github.com:org/my-repo.git
    try:
        origin = repo.get_config()[('remote', 'origin')]['url']
        dotgit = origin.split('/')[-1]
        return dotgit.replace('.git', '')
    except KeyError, IndexError:
        pass

    # 2. use repo directory path
    try:
        return repo.path.split('/')[-1]
    except:
        pass


def get_existing_deployment(name):
    return Deployment.objects(kube_api).get_or_none(name=name)


def kube_template(template, app):
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../templates')
    with open('{}/{}.yaml'.format(template_path, template)) as tpl:
        return Template(tpl.read()).render(dict(app=app))


def from_deployment(deployment):
    click.echo("Found an existing deployment for `{}` in `{}`:".format(
        name, kube_api.config.current_context))
    service = Service.objects(kube_api).get_or_none(name=name)

    config = Config.from_kubernetes(deployment, service)

    click.echo("App name: {}".format(config.app.name))
    click.echo("App docker: {}".format(config.app.docker))
    click.echo("App tag: {}".format(config.app.tag))
    if config.app.port:
        click.echo("App port: {}".format(config.app.port))
    if config.app.dns_name:
        click.echo("App DNS: {}".format(config.app.dns_name))
    if config.app.ssl_cert:
        click.echo("App SSL certificate: {}".format(config.app.ssl_cert))
    if click.confirm("Save configuration to `.kyber/config`?"):
        config.save(kube_api.config.current_context)
    sys.exit(0)


def from_scratch(name, repo):
    docker = click.prompt("Enter base docker name (e.g. ...dkr.ecr.us-east-1.amazonaws.com/{})".format(name))
    port = click.prompt("Enter app port (e.g. 5000)")
    tag = click.prompt("Enter tag", default='git_{}'.format(repo.head()))
    dns_name = click.prompt("Enter DNS name (enter for none)", default=None)
    ssl_cert = click.prompt("Enter SSL certificate ARN (enter for none)", default=None)
    app = App(name, docker, tag, port, dns_name, ssl_cert)
    return app


def initialize():
    context = kube_api.config.current_context
    try:
        config = Config.from_file('.kyber/config', context)
    except ContextNotFound:
        pass
    else:
        raise InitError("Found .kyber/config with entry for `{}`, exiting".format(context))

    cwd = os.path.abspath('.')
    repo = git.Repo(cwd)
    name = get_default_name(repo)
    if name is None:
        click.prompt("Unable to derive a name from the current git repository or directory!")
        sys.exit(1)

    deployment = get_existing_deployment(name)
    if deployment is not None:
        return from_deployment(deployment)

    click.echo("Did not find an existing deployment for `{}` in `{}`".format(name, context))
    if click.confirm("Create one?", abort=True):
        app = from_scratch(name, repo)
        click.echo("Creating..")
        print kube_template('deployment', app)
        print kube_template('service', app)
        print kube_template('secrets', app)
