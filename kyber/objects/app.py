class App(object):
    name = None
    docker = None
    tag = None
    port = None
    dns_name = None
    ssl_cert = None
    secret = None

    def __init__(self, name, docker, tag, port=None, dns_name=None, ssl_cert=None):
        self.name = name
        self.docker = docker
        self.tag = tag
        self.port = int(port) if port is not None else None
        self.dns_name = dns_name
        self.ssl_cert = ssl_cert  # AWS ARN

    def to_dict(self):
        return dict((k, v) for (k, v) in
            dict(
                name=self.name,
                docker=self.docker,
                tag=self.tag,
                port=self.port,
                ssl_cert=self.ssl_cert,
                dns_name=self.dns_name).iteritems()
            if v is not None)

    @property
    def image(self):
        return "{}:{}".format(self.docker, self.tag)
