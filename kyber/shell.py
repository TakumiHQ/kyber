import click
import os
from pykube.objects import Pod
from kyber.lib.kube import kube_api
from kyber.utils import get_executable_path


def run(name, shell_path):
    for pod in Pod.objects(kube_api).filter(selector={'app': name}).iterator():
        if pod.ready:  # use the first ready pod, otherwise we use the last pod
            break

    click.echo("Running shell in pod `{}` in kube ctx `{}`".format(
               pod.name, kube_api.config.current_context))
    os.execve(get_executable_path('kubectl'), ["kubectl", "exec", "-i", "-t", pod.name, shell_path], os.environ)
