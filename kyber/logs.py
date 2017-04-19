import click
import heapq
import iso8601
import itertools
import time

from pykube.objects import Pod, ObjectDoesNotExist
from kyber.lib.kube import kube_api


class PriorityQueue(object):
    """ Basic priority queue backed by a heap + a counter to tiebreak same-priority
    values.
    """
    def __init__(self):
        self.heap = []
        self.counter = itertools.count()

    @property
    def count(self):
        return len(self.heap)

    @property
    def empty(self):
        return self.count == 0

    def push(self, priority, value):
        heapq.heappush(self.heap, (priority, next(self.counter), value))

    def pop(self):
        return heapq.heappop(self.heap)


def parse_logentry(logentry):
    """ Parse a log entry of fmt: `<iso8601> <log string>\n`

    returns (unixtimestamp, logentry)
    """
    iso_ts, rest = logentry.split(' ', 1)
    ts = time.mktime(iso8601.parse_date(iso_ts).timetuple())
    return (ts, rest)


class OrderedLog(PriorityQueue):
    """ store log entries in a heap ordered by the timestamp
    - can optionally keep the timestamp as part of the log string
    - can warn if unable to parse a timestamp, in which case all log entries
      get the same priority (0) as no timestamp could be found.
    """
    def __init__(self, keep_timestamp=None, verbose=None):
        if keep_timestamp is None:
            keep_timestamp = False
        if verbose is None:
            verbose = False

        self.keep_timestamp = keep_timestamp
        self.verbose = verbose

        super(OrderedLog, self).__init__()

    def push(self, pod, logentry):
        try:
            (ts, logstring) = parse_logentry(logentry)
        except Exception as e:
            if self.verbose:
                click.echo(u"Can't parse iso8601 timestamp from `{}`, falling back to ts (priority) 0."
                           u"Error: {}".format(logentry, e))
            (ts, logstring) = 0, logentry

        store_string = '{pod}: {entry}'.format(
            pod=pod,
            entry=logentry if self.keep_timestamp else logstring
        )
        super(OrderedLog, self).push(ts, store_string)

    def pop(self):
        (ts, priority, string) = super(OrderedLog, self).pop()
        return string


def get(app, pod=None):
    pods = []
    if pod is None:
        for pod in Pod.objects(kube_api).filter(selector={'app': app}).iterator():
            pods.append(pod)
    else:
        try:
            pods.append(Pod.objects(kube_api).get_by_name(pod))
        except ObjectDoesNotExist:
            click.echo(u"Can't find a pod named `{}`".format(pod))

    ols = OrderedLog(keep_timestamp=True)
    for pod in pods:
        pod_logs = pod.logs(timestamps=True, since_seconds=3600)
        for line in pod_logs.split('\n'):
            ols.push(pod.name, line)

    while not ols.empty:
        click.echo(ols.pop())
