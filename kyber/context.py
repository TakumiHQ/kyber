import click
import dulwich
import os
import sys
import yaml
from functools import wraps

name = None
docker = None
tag = None
target = None
dirty = None
dirty_reason = None


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
    tag = None              # git HEAD commit (deployment tag)
    target = None           # kubectl context
    git_dirty = False       # is the git repo dirty? (we only deploy built images)
    _git_status = None

    def __init__(self, checks=None):
        tasks = dict(
            config=self.load_config,
            git_tag=self.git_tag,
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
            raise ContextError("No configuration found for kube context `{}` in kyber context.  Forgot to run 'kb init'?".format(kube_ctx))

        self.name = cfg[kube_ctx]['name']
        self.docker = cfg[kube_ctx]['docker']
        self.port = cfg[kube_ctx]['port']

    def git_status(self):
        from dulwich import porcelain as git
        try:
            status = git.status()
        except dulwich.errors.NotGitRepository:
            raise ContextError("{} is not a valid git repository".format(self.cwd))

        for state in ('add', 'modify', 'delete'):
            if status.staged[state]:
                self.is_dirty = True
                break
        if status.unstaged:
            self.is_dirty = True
        self._git_status = status

    def git_tag(self):
        from dulwich import porcelain as git
        repo = git.Repo(self.cwd)
        self.tag = 'git_{}'.format(repo.head())

    def export(self):
        global name, docker, tag, target, dirty, dirty_reason
        name = self.name
        docker = self.docker
        tag = self.tag
        target = self.target
        dirty = self.git_dirty
        dirty_reason = self._git_status


def required(**ctx_kwargs):
    def wrapper(fn, *args, **kwargs):
        @wraps(fn)
        def inner(*args, **kwargs):
            try:
                ctx = Context(**ctx_kwargs)
                ctx.export()
            except ContextError as e:
                click.echo("Unable to load kyber context: {}".format(e.message))
                sys.exit(1)

            return fn(*args, **kwargs)
        return inner
    return wrapper


__all__ = [required, name, docker, tag, target, dirty, dirty_reason]
