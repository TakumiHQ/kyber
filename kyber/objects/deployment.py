import pykube

LINKED_DEPLOYMENT_KEY_PREFIX = 'kyber.linked.deployment'


class Deployment(pykube.Deployment):
    @property
    def ready(self):
        if "status" in self.obj:
            if "updatedReplicas" in self.obj["status"]:
                return super(Deployment, self).ready
        return False

    @property
    def generation(self):
        try:
            return self.obj['status']['observedGeneration']
        except KeyError:
            return 0

    def linked_deployments(self):
        for key in self.annotations.keys():
            if key.startswith(LINKED_DEPLOYMENT_KEY_PREFIX):
                yield self.annotations[key]

    def __repr__(self):
        return "<Deployment {}>".format(self.name)
