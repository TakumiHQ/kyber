""" kyber.deploy - logic and cli commands related to deploying a kyber project.
"""
import json
import pykube


class App(object):
    name = None
    docker = None
    tag = None
    def __init__(self, name, docker, tag):
        self.name = name
        self.docker = docker
        self.tag = tag

    @property
    def image(self):
        return "{}:{}".format(self.docker, self.tag)

    def container_spec(self):
        return dict(
            spec=dict(
                template=dict(
                    spec=dict(
                        containers=[
                            dict(
                                image=self.image
                            )
                        ]
                    )
                )
            )
        )

    def metadata_spec(self, set_date=False):
        # XXX: add "kyber_managed=True" in labels / metadata?
        spec_tpl = dict(
            metadata=dict(
                labels=dict(
                    app=self.name,
                    tag=self.tag,
                )
            )
        )
        if set_date:
            spec_tpl['metadata']['labels']['data'] = dt.datetime.now().isoformat()
        return dict(spec=dict(template=spec_tpl))

    def get_spec(self, set_date=False):
        spec = self.container_spec()
        spec.update(self.metadata_spec(set_date))
        return spec


def execute(app, force=False):
    config = pykube.KubeConfig.from_file("~/.kube/config")
    api = pykube.HTTPClient(config)
    deployment = pykube.Deployment.objects(api).filter(
        name=app.name
    ).get()
    new_spec = app.get_spec(set_date=force)
    print new_spec
    return
    deployment.set_obj(app.get_spec(set_date=force))
    deployment.update()
