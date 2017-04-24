import pykube

from six.moves.urllib.parse import urlencode


class Pod(pykube.Pod):
    """ An extended version of the pykube Pod object which can stream logs """
    def logs(self, container=None, pretty=None, previous=False,
             since_seconds=None, since_time=None, timestamps=False,
             tail_lines=None, limit_bytes=None, follow=None):
        """
        Produces the same result as calling kubectl logs pod/<pod-name>.
        Check parameters meaning at
        http://kubernetes.io/docs/api-reference/v1/operations/,
        part 'read log of the specified Pod'. The result is plain text.
        """
        log_call = "log"
        params = {}
        if container is not None:
            params["container"] = container
        if pretty is not None:
            params["pretty"] = pretty
        if previous:
            params["previous"] = "true"
        if since_seconds is not None and since_time is None:
            params["sinceSeconds"] = int(since_seconds)
        elif since_time is not None and since_seconds is None:
            params["sinceTime"] = since_time
        if timestamps:
            params["timestamps"] = "true"
        if tail_lines is not None:
            params["tailLines"] = int(tail_lines)
        if limit_bytes is not None:
            params["limitBytes"] = int(limit_bytes)
        if follow is not None:
            params["follow"] = bool(follow)

        query_string = urlencode(params)
        log_call += "?{}".format(query_string) if query_string else ""
        kwargs = {
            "version": self.version,
            "namespace": self.namespace,
            "operation": log_call,
            "stream": follow is True,
        }
        if follow is None or follow is False:
            r = self.api.get(**self.api_kwargs(**kwargs))
            r.raise_for_status()
            return r.text
        else:
            r = self.api.get(**self.api_kwargs(**kwargs))
            r.raise_for_status()
            return r
