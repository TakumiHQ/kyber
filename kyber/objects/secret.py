import base64
import json
import pykube


class Secret(pykube.Secret):
    """ kubernetes secrets wrapper, implements almost complete dict interface
    and automatically base64 encodes/decodes values to maintain them as base64
    in kubernetes, while hiding that fact from the user.
    """
    def __init__(self, *args, **kwargs):
        super(pykube.Secret, self).__init__(*args, **kwargs)
        if 'data' not in self.obj:
            self.obj['data'] = dict()

    def __setitem__(self, key, item):
        self.obj['data'][key] = base64.b64encode(item)

    def __getitem__(self, key):
        return base64.b64decode(self.obj['data'][key])

    def __delitem__(self, key):
        del self.obj['data'][key]

    def __len__(self):
        return len(self.obj['data'])

    def __cmp__(self, dict_):
        return cmp(self.obj['data'], dict_)

    def __contains__(self, item):
        return item in self.obj['data']

    def __iter__(self):
        return iter(self.obj['data'])

    def __repr__(self):
        return "<Secret {}: {}>".format(self.name, repr(self.obj['data']))

    def __unicode__(self):
        return unicode(repr(self))

    def has_key(self, k):
        return self.obj['data'].has_key(k)  # noqa

    def keys(self):
        return self.obj['data'].keys()

    def values(self):
        return self.obj['data'].values()

    def items(self):
        return self.obj['data'].items()

    def iteritems(self):
        return self.obj['data'].iteritems()

    def pop(self, *args, **kwargs):
        return self.obj['data'].pop(*args, **kwargs)

    def update(self):
        """ Overload the pykube .update because it uses PATCH, while we
        basically want PUT, so we can delete variables from the secret.
        """
        r = self.api.put(**self.api_kwargs(
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.obj),
        ))
        self.api.raise_for_status(r)
        self.set_obj(r.json())
