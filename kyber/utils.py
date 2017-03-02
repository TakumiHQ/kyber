import sh
import time


class TimeIt(object):
    """ A utility class to time operations -- useful when debugging slow commands.
    Usage:
        with TimeIt("something"):
            do_some_work()
        >>>
            something: took 0.000012098012994s

        or
        checks = ['config', 'git_status', 'git_tag']
        for check in checks:
            with TimeIt("Doing {}".format(check)):
                tasks[check]()
        >>>
            config: took 0.00685501098633s
            git_status: took 0.42912197113s
            git_tag: took 0.000161170959473s
    """
    def __init__(self, name):
        self.name = name

    def __enter__(self, *args, **kwargs):
        self.start_t = time.time()

    def __exit__(self, *args, **kwargs):
        self.end_t = time.time()
        print "{}: took {}s".format(self.name, self.end_t - self.start_t)


def get_executable_path(executable):
    path = sh.which(executable)
    if path is None:
        raise Exception("Can't find '{}' executable, is it in your $PATH?".format(executable))
    return str(path)
