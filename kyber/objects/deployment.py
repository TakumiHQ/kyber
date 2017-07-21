import pykube


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

    def __repr__(self):
        return "<Deployment {}>".format(self.name)
