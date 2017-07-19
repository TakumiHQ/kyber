import click
import dulwich
import os
import sys
import yaml
from functools import wraps


class ContextError(Exception):
    pass


class Context(object):
    """ A Context object represents the current kyber context, derived from a combination of:
    - the app config found in $CWD/.kyber/config
    - the git repo in $CWD
    - the current kubectl context
    """
    name = None             # current app name
    docker = None           # docker image (repo/app)
    port = None             # app port (not used?) XXX
    git_hash = None         # git HEAD commit
    target = None           # kubectl context
    git_dirty = False       # is the git repo dirty? (we only deploy built images)
    _git_status = None

    def __init__(self, checks=None):
        tasks = dict(
            config=self.load_config,
            git_tag=self.set_git_hash,
            git_status=self.git_status,
        )
        if checks is None:
            checks = ['config', 'git_tag', 'git_status']

        self.cwd = os.path.abspath('.')
        for task in checks:
            tasks[task]()

    def load_config(self):
        cfg_name = os.path.join(self.cwd, '.kyber/config')
        try:
            with open(cfg_name) as app_config:
                cfg = yaml.load(app_config.read())
        except IOError:
            raise ContextError("Not working within a kyber context (can't read {})".format(
                cfg_name))
        except yaml.ParserError:
            raise ContextError("YAML parsing failed for '{}', unable to load context".format(
                cfg_name))

        from kyber.lib.kube import kube_api
        kube_ctx = kube_api.config.current_context
        if kube_ctx not in cfg:
            raise ContextError(("No configuration found for kube context `{}` in kyber context."
                                " Forgot to run 'kb init'?").format(kube_ctx))

        self.kube_ctx = kube_api.config.contexts[kube_ctx]
        self.kube_ctx['name'] = kube_ctx
        self.name = cfg[kube_ctx]['name']
        self.docker = cfg[kube_ctx]['docker']
        self.port = cfg[kube_ctx]['port']

    def git_status(self):
        from dulwich import porcelain as git
        try:
            repo = git.Repo.discover()
            status = git.status(repo=repo)
        except dulwich.errors.NotGitRepository:
            raise ContextError("{} is not a valid git repository".format(self.cwd))

        for state in ('add', 'modify', 'delete'):
            if status.staged[state]:
                self.is_dirty = True
                break
        if status.unstaged:
            self.is_dirty = True
        self._git_status = status

    def set_git_hash(self, git_hash=None):
        if git_hash is None:
            from dulwich import porcelain as git
            git_hash = git.Repo.discover(self.cwd).head()
        else:
            git_hash = git_hash.replace('git_', '')

        self.git_hash = git_hash

    @property
    def tag(self):
        return 'git_{}'.format(self.git_hash)


def required(**ctx_kwargs):
    def wrapper(fn, *args, **kwargs):
        @wraps(fn)
        def inner(*args, **kwargs):
            try:
                ctx = Context(**ctx_kwargs)
                kwargs['ctx'] = ctx
            except ContextError as e:
                click.echo("Unable to load kyber context: {}".format(e.message))
                sys.exit(1)

            return fn(*args, **kwargs)
        return inner
    return wrapper
