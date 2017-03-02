import click
import os
from urlparse import urlparse, urlunparse

from kyber.context import Context, ContextError
from kyber.utils import get_executable_path


def _kube_dash_base_url(cfg):
    url = urlparse(cfg.cluster['server'])
    try:
        username = cfg.user['username']
        password = cfg.user['password']
        url = url._replace(netloc='{}:{}@{}'.format(username, password, url.netloc))
    except KeyError:  # no username/pass in kube context?
        pass
    return url


def service_dashboard(cfg, name):
    path = ("/api/v1/proxy/namespaces/kube-system/services/kubernetes-dashboard/"
            "#/service/{namespace}/{app_name}?namespace={namespace}").format(
                namespace=cfg.namespace, app_name=name)
    return urlunparse(_kube_dash_base_url(cfg)._replace(path=path))


def namespace_dashboard(cfg):
    path = ("/api/v1/proxy/namespaces/kube-system/services/kubernetes-dashboard/"
            "#/pod?namespace={namespace}").format(namespace=cfg.namespace)
    return urlunparse(_kube_dash_base_url(cfg)._replace(path=path))


def launch(cfg=None, executor=None):
    if cfg is None:
        from kyber.lib.kube import kube_api
        cfg = kube_api.config
    if executor is None:
        executor = os.execve

    try:
        context = Context()
        click.echo("Opening dashboard for `{}` in `{}`".format(context.name, cfg.namespace))
        url = service_dashboard(cfg, context.name)
    except ContextError:  # fall back to opening the kubernetes dashboard
        click.echo("Not in a kyber context, showing dash for k8s pods in `{}`".format(cfg.namespace))
        url = namespace_dashboard(cfg)

    try:
        executor(get_executable_path('open'), ["open", url], os.environ)
    except Exception as e:
        click.echo("Unable to launch dashboard automatically ({})".format(e.message))
        click.echo("URL: {}".format(url))
