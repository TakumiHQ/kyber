import click
import iso8601
import itertools
import threading
import time
import Queue

from pykube.objects import ObjectDoesNotExist
from kyber.lib.kube import kube_api
from kyber.objects import Pod


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

        if isinstance(logentry, basestring):
            item = '{pod}: {entry}'.format(
                pod=pod,
                entry=logentry if self.keep_timestamp else logstring
            )
        else:
            item = logentry

        self.pq.put((ts, next(self.counter), item))

    def get_raw(self, *args, **kwargs):
        return self.pq.get(*args, **kwargs)

    def get(self, *args, **kwargs):
        """ Return just the item, but pass on *args and **kwargs
        to allow timeouts, etc """
        (priority, index, item) = self.pq.get(*args, **kwargs)
        return item


class LogStream(object):
    def __init__(self, pod, source):
        self.pod = pod
        self.source = source

    def __repr__(self):
        return u'<LogStream({})>'.format(self.pod)


class LogMultiplexer(object):
    """ adapted from http://www.dabeaz.com/generators/genmulti.py
    setting all threads to daemon so they'll get mercilessly killed on SIGINT / SIGTERM
    """
    def __init__(self, queue):
        self.queue = queue
        self.streams = []
        self.threads = []
        self.master = threading.Thread(target=self.run_all)
        self.master.daemon = True

    def add_stream(self, pod, stream):
        self.streams.append(LogStream(pod, stream))

    def run_one(self, stream):
        for item in stream.source:
            self.queue.put(stream.pod, item)

    def run_all(self):
        for stream in self.streams:
            t = threading.Thread(target=self.run_one, args=(stream, ))
            t.daemon = True
            t.start()
            self.threads.append(t)

        for t in self.threads:
            t.join()
        self.queue.put('', StopIteration)

    def start(self):
        self.master.start()

    def get(self):
        while True:
            item = self.queue.get()
            if item is StopIteration:
                self.master.join()
                return
            yield item


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
    multiplexer = LogMultiplexer(queue)
    for pod in pods:
        pod_logs = pod.logs(since_seconds=since_seconds, timestamps=True, follow=follow)
        multiplexer.add_stream(pod.name, pod_logs)
    multiplexer.start()
    for entry in multiplexer.get():
        click.echo(entry)
