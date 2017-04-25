import pykube

from six.moves.urllib.parse import urlencode


class Pod(pykube.Pod):
    """ An extended version of the pykube Pod object which can stream logs """

    @staticmethod
    def _log_params(container, pretty, previous, since_seconds, since_time,
                    timestamps, tail_lines, limit_bytes, follow):
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
        return params

    def logs(self, container=None, pretty=None, previous=False,
             since_seconds=None, since_time=None, timestamps=False,
             tail_lines=None, limit_bytes=None, follow=None):
        """
        Produces the same result as calling kubectl logs pod/<pod-name>.
        Check parameters meaning at
        http://kubernetes.io/docs/api-reference/v1/operations/,
        part 'read log of the specified Pod'. Returns a line iterator.
        """
        log_call = "log"
        query_string = urlencode(
            self._log_params(
                container, pretty, previous, since_seconds, since_time, timestamps, tail_lines, limit_bytes, follow
            )
        )
        log_call += "?{}".format(query_string) if query_string else ""
        kwargs = {
            "version": self.version,
            "namespace": self.namespace,
            "operation": log_call,
            "stream": follow is True,
        }
        r = self.api.get(**self.api_kwargs(**kwargs))
        r.raise_for_status()
        return r.iter_lines(chunk_size=16)  # default is 512, this might be too small
