import click
import iso8601
import itertools
import time
import Queue

from pykube.objects import ObjectDoesNotExist
from kyber.lib.kube import kube_api
from kyber.objects import Pod
from kyber.utils import multiplex


def parse_logentry(logentry):
    """ Parse a log entry of fmt: `<iso8601> <log string>\n`

    returns (unixtimestamp, logentry)
    """
    iso_ts, rest = logentry.split(' ', 1)
    ts = time.mktime(iso8601.parse_date(iso_ts).timetuple())
    return (ts, rest)


class TimestampOrderedQueue(object):
    """
    Stores log entries in a PriorityQueue and calculates the priority
    from an iso8601 timestamp at the beginning of every logentry.
    Values are returned in an oldest-first order, and equal timestamps
    are returned FIFO.

    - can optionally keep the timestamp as part of the log string
    - can warn if unable to parse a timestamp, in which case all log entries
      get the same priority (0) as no timestamp could be found.
    """
    def __init__(self, keep_timestamp=None, verbose=None):
        self.pq = Queue.PriorityQueue()
        self.counter = itertools.count()

        if keep_timestamp is None:
            keep_timestamp = False
        if verbose is None:
            verbose = False

        self.keep_timestamp = keep_timestamp
        self.verbose = verbose

    @property
    def count(self):
        return self.pq.qsize()

    @property
    def empty(self):
        return self.pq.empty()

    def put(self, pod, logentry):
        try:
            (ts, logstring) = parse_logentry(logentry)
        except Exception as e:
            if self.verbose:
                click.echo(u"Can't parse iso8601 timestamp from `{}`, falling back to ts (priority) 0."
                           u"Error: {}".format(logentry, e))
            (ts, logstring) = 0, logentry

        store_string = format_log_string(pod, logentry, logstring, self.keep_timestamp)
        self.pq.put((ts, next(self.counter), store_string))

    def get_raw(self, *args, **kwargs):
        return self.pq.get(*args, **kwargs)

    def get(self, *args, **kwargs):
        """ Return just the formatted string, but pass on *args and **kwargs
        to allow timeouts, etc """
        (priority, index, string) = self.pq.get(*args, **kwargs)
        return string


def format_log_string(pod, logentry, logstring, keep_timestamp):
    return '{pod}: {entry}'.format(
        pod=pod,
        entry=logentry if keep_timestamp else logstring
    )


def get(app, pod, since_seconds, keep_timestamp, follow):
    pods = []
    if pod is None:
        for pod in Pod.objects(kube_api).filter(selector={'app': app}).iterator():
            pods.append(pod)
    else:
        try:
            pods.append(Pod.objects(kube_api).get_by_name(pod))
        except ObjectDoesNotExist:
            click.echo(u"Can't find a pod named `{}`".format(pod))

    queue = TimestampOrderedQueue(keep_timestamp)
    kwargs = {'since_seconds': since_seconds, 'timestamps': True}
    for pod in pods:
        pod_logs = pod.logs(**kwargs)
        for line in pod_logs:
            queue.put(pod.name, line)

    while not queue.empty:
        click.echo(queue.get())

    if follow is True:
        elapsed = 30
        kwargs['follow'] = follow
        kwargs['since_seconds'] = elapsed
        streams = [pod.logs(**kwargs) for pod in pods]
        labels = [pod.name for pod in pods]

        for pod, message in multiplex(streams, labels):
            click.echo(format_log_string(pod, message, message, keep_timestamp))
