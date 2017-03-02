import click
import os


def write_envdir(cfg, target_dir):
    for param in sorted(cfg.keys()):
        with open(os.path.join(target_dir, param), "w") as out:
            out.write("{}".format(cfg[param]))


def read_envdir(source_dir):
    config = dict()
    for param in os.listdir(source_dir):
        with open(os.path.join(source_dir, param)) as fp:
            config[param] = fp.read().rstrip("\n")
    return config


def read_envfile(source_file):
    config = dict()
    with open(source_file) as fp:
        for line in fp.readlines():
            key, value = line.split("=", 1)
            config[key] = value.rstrip("\n")
    return config


def save_secret(env, cfg_vars):
    if env.secret is None:
        if click.confirm("{} is missing a Secret object, create one?".format(env)):
            env.sync()
        else:
            click.echo("Exiting, can't load values into a non-existent object")
            return
    for key, value in cfg_vars.iteritems():
        env.secret[key] = value
    env.secret.update()
