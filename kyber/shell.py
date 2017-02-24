import click
import os
import sh
from pykube.objects import Pod
from kyber.lib.kube import kube_api


def get_kubectl_path():
    path = sh.which('kubectl')
    if path is None:
        raise Exception("Can't find kubectl executable, is it in your $PATH?")
    return str(path)


def run(name):
    ready = False
    for pod in Pod.objects(kube_api).filter(selector={'app': 'takumi-server'}).iterator():
        if pod.ready:  # use the first ready pod, otherwise we use the last pod
            break

    click.echo("Running shell in pod `{}` in kube ctx `{}`".format(
       pod.name, kube_api.config.current_context))
    os.execve(get_kubectl_path(), ["kubectl", "exec", "-i", "-t", pod.name, "/bin/bash"], os.environ)
