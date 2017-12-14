import click
import os
import pwd
from pykube.objects import Pod
from kyber.lib.kube import kube_api
from kyber.utils import get_executable_path




def run(name, shell):
    for pod in Pod.objects(kube_api).filter(selector={'app': name}).iterator():
        if pod.ready:  # use the first ready pod, otherwise we use the last pod
            break

    def env_vars():
        d = {
            'KYBER_USER': pwd.getpwuid(os.getuid()).pw_name,
            'KYBER_POD': pod.name,
            'KYBER_APP': name,
            'KYBER_KUBECTL_CONTEXT': kube_api.config.current_context,
        }
        return " ".join(["{}={}".format(key, val) for key, val in d.iteritems()])

    cmd = '{env} {shell}'.format(env=env_vars(), shell=shell)

    click.echo("Running shell in pod `{}` in kube ctx `{}`".format(
               pod.name, kube_api.config.current_context))
    os.execve(
        get_executable_path('kubectl'),
        ["kubectl", "exec", "-i", "-t", pod.name, '--', shell, '-c', cmd],
        os.environ
    )
