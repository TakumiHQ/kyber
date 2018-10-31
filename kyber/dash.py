import json
import subprocess
from urllib.parse import urljoin

import click

from kyber.context import Context, ContextError


def service_dashboard(cfg, name):
    path = (
        "/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:"
        "/proxy/#!/service/{namespace}/{app_name}?namespace={namespace}"
    ).format(namespace=cfg.namespace, app_name=name)
    return urljoin("http://localhost:8001", path)


def namespace_dashboard(cfg):
    path = (
        "/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:"
        "/proxy/#!/overview?namespace={namespace}"
    ).format(namespace=cfg.namespace)
    return urljoin("http://localhost:8001", path)


def _get_token(cfg):
    user = cfg.user
    if "exec" not in user:
        return

    args = user["exec"]["args"]
    args.insert(0, user["exec"]["command"])

    try:
        response = subprocess.check_output(args)
        parsed = json.loads(response)
    except Exception as e:
        click.echo("Unable to get token ({})".format(e))
        return

    return parsed.get("status", {}).get("token")


def launch(cfg=None, executor=None):  # noqa: C901
    if cfg is None:
        from kyber.lib.kube import kube_api

        cfg = kube_api.config

    if executor is None:
        executor = subprocess

    token = _get_token(cfg)
    if token:
        click.echo("Your login token:\n\n{}\n".format(token))

    click.echo("Starting kubectl proxy")
    try:
        proxy = executor.Popen(["kubectl", "proxy"])
    except Exception as e:
        click.echo("Unable to start kubectl proxy ({})".format(e))
        proxy = None

    try:
        context = Context()
        click.echo(
            "Opening dashboard for `{}` in `{}`".format(context.name, cfg.namespace)
        )
        url = service_dashboard(cfg, context.name)
    except ContextError:  # fall back to opening the kubernetes dashboard
        click.echo(
            "Not in a kyber context, showing dash for k8s pods in `{}`".format(
                cfg.namespace
            )
        )
        url = namespace_dashboard(cfg)

    try:
        executor.call(["open", url])
    except Exception as e:
        click.echo("Unable to launch dashboard automatically ({})".format(e))
        click.echo("URL: {}".format(url))

    if proxy is not None:
        proxy.wait()
