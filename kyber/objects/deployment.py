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

    @property
    def available_replicas(self):
        if not self.ready:
            return 0
        return self.obj['status']['availableReplicas']

    @property
    def updated_replicas(self):
        if not self.ready:
            return 0
        return self.obj['status']['updatedReplicas']

    def __repr__(self):
        return "<Deployment {}>".format(self.name)
