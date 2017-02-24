import click
import os
import sh
from pykube.objects import Pod
from kyber.lib.kube import kube_api


def get_kubectl_path():
    path = sh.which('kubectl')
    if path is None:
        raise Exception("kubectl not in $PATH !?")
    return str(path)


def exec_shell(pod):
    os.execve(get_kubectl_path(), ["kubectl", "exec", "-i", "-t", pod.name, "/bin/bash"], os.environ)


def run(name):
    ready = False
    for pod in Pod.objects(kube_api).filter(selector={'app': 'takumi-server'}).iterator():
        if pod.ready:
            click.echo("Choosing pod: {}".format(pod))
            ready = True
            break

    if not ready:
        click.echo("Choosing pod: {} (not ready, no pods are ready!)".format(pod))

    exec_shell(pod)
