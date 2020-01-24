import base64
import json
import pykube


def b64_decode(s):
    if isinstance(s, str):
        s = s.encode('utf-8')
    decoded = base64.b64decode(s)
    return decoded.decode('utf-8')


def b64_encode(s):
    if isinstance(s, str):
        s = s.encode('utf-8')
    encoded = base64.b64encode(s)
    return encoded.decode('utf-8')


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
        self.obj['data'][key] = b64_encode(item)

    def __getitem__(self, key):
        return b64_decode(self.obj['data'][key])

    def __delitem__(self, key):
        del self.obj['data'][key]

    def __len__(self):
        return len(self.obj['data'])

    def __cmp__(self, dict_):
        return (self.obj['data'] > dict_) - (self.obj['data'] < dict_)

    def __contains__(self, item):
        return item in self.obj['data']

    def __iter__(self):
        return iter(self.obj['data'])

    def __repr__(self):
        return "<Secret {}: {}>".format(self.name, repr(self.obj['data']))

    def __unicode__(self):
        return str(repr(self))

    def has_key(self, k):
        return k in self.obj['data']  # noqa

    def keys(self):
        return list(self.obj['data'].keys())

    def values(self):
        return list(self.obj['data'].values())

    def items(self):
        return list(self.obj['data'].items())

    def iteritems(self):
        return iter(self.obj['data'].items())

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
