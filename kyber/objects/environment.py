import click
import pkgutil
import yaml
from jinja2 import Template

from pykube.objects import Service

from kyber.objects.app import App
from kyber.objects.deployment import Deployment
from kyber.objects.secret import Secret

from kyber.lib.kube import kube_api

object_cls = dict(
    deployment=Deployment,
    service=Service,
    secret=Secret,
)


def kube_from_template(template, app):
    raw_tpl = pkgutil.get_data('kyber', 'templates/{}.yaml'.format(template))
    cooked_tpl = Template(raw_tpl).render(dict(app=app))
    return yaml.load(cooked_tpl)


class Environment(object):
    """ A wrapper object around the necessary kubernetes objects to run a kyber app """
    deployment = None
    service = None
    secret = None

    def __init__(self, name):
        self.name = name
        self.deployment = Deployment.objects(kube_api).get_or_none(name=name)
        self.service = Service.objects(kube_api).get_or_none(name=name)
        self.secret = Secret.objects(kube_api).get_or_none(name=name)
        self.app = self.app_from_objects()

    def status(self):
        for name, obj in self.kube_objects.iteritems():
            click.echo("[{}] {}".format('X' if obj is not None else ' ', name))

    def app_from_objects(self):
        """ Create an App object by finding the relevant data in kubernetes
        Deployment, Service (and later Secrets) objects.
        """
        if self.deployment is None:
            return None

        metadata = self.deployment.obj['spec']['template']['metadata']
        spec = self.deployment.obj['spec']['template']['spec']

        name = metadata['labels']['app']
        docker, tag = spec['containers'][0]['image'].split(":", 2)
        port = spec['containers'][0]['ports'][0].get('containerPort')
        app = App(name, docker, tag, port)
        app.secret = self.secret

        if self.service is not None:
            metadata = self.service.obj['metadata']
            if 'dns' in metadata['labels']:
                dns_name = metadata['annotations']['domainName']
                app.dns_name = dns_name
            if 'service.beta.kubernetes.io/aws-load-balancer-ssl-cert' in metadata['annotations']:
                app.ssl_cert = metadata['annotations']['service.beta.kubernetes.io/aws-load-balancer-ssl-cert']
        return app

    def sync(self):
        if self.app is None:
            raise Exception("Can't sync environment without an app!")
        for name, obj in self.kube_objects.iteritems():
            cls = object_cls[name]
            new = cls(kube_api, kube_from_template(name, self.app))
            if obj is None:
                new.create()
            else:
                print "Updating {}".format(name), new.obj
                new.update()

    @property
    def kube_objects(self):
        return dict(
            deployment=self.deployment,
            service=self.service,
            secret=self.secret
        )

    @property
    def missing_objects(self):
        return dict((name, obj,) for (name, obj) in self.kube_objects.iteritems() if obj is None)

    @property
    def complete(self):
        return len(self.missing_objects) == 0

    def __repr__(self):
        return "<Environment:{} @ {}>".format(self.name, kube_api.config.current_context)
