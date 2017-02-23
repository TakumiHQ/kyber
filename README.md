# kyber

kyber is an opinionated wrapper around ECR-backed kubernetes deployments.

## initialize a project

(kb: dev) my-project (master) $ kb init
Did not find an existing deployment for `my-project` in `dev`:
Create one? [y/N]

    .. prompt for name, docker (registry), port, external dns?
    ... created deployment: my-project in `dev`
    ... created service: my-project
    ... created secret: my-project-cfg


## deploy a project

    (kb: dev) my-project (master) $ kb deploy [<tag defaults to tip of current branch>]
    ...


## configure project config (secrets)

### list

    (kb: dev) my-project (master) $ kb config list
    SOME=variables
    ARE=more
    EQUAL=than
    OTHERS=100

### get

    (kb: dev) my-project (master) $ kb config get<TAB>
    ARE SOME EQUAL OTHERS
    (kb: dev) my-project (master) $ kb config get ARE
    more

### set

    (kb: dev) my-project (master) $ kb config set OTHERS 99%
    (kb: dev) my-project (master) $ kb config get OTHERS
    99%


### unset

    (kb: dev) my-project (master) $ kb config unset OTHERS
    Do you wish to delete config variable my-project.OTHERS with value of `99%` [y/N]:
    (kb: dev) my-project (master) $ kb config get OTHERS
    No var found for `my-project.OTHERS`


### envdir

	(kb: dev) my-project $ kb config envdir .env-dev-copy
	found 4 vars, will write to `/Users/ses/w/my-project/.env-dev-copy/*` [y/N]: y

### load

Loads a local environment from either an envfile or a .envdir (as used by runit's `chpst` and
daemontools's `envdir`).

	(kb: dev) my-project $ kb config load .env-dev-copy
	Found 4 vars in `/Users/ses/w/my-project/.env-dev-copy/` do you wish to write them to <Environment:my-project @ dev> [y/N]

It detects whether the given argument is a file or a directory:

	(kb: dev) my-project $ kb config list > end-dev-copy
	(kb: dev) my-project $ kb config load env-dev-copy
	Found 4 vars in `/Users/ses/w/my-project/env-dev-copy` do you wish to write them to <Environment:my-project @ dev> [y/N]

# see project deployment status

    (kb: dev) my-project (master) $ kb status
    Project: my-project
    Docker: 12345.dkr.ecr.us-east-1.amazonaws.com/takumi-server
    Deployed tag: git_6eea5482b7f55823f86a63d9ddf6d84ec6769a78
    Current tag: git_6eea5482b7f55823f86a63d9ddf6d84ec6769a78 [deployable: y]

# run a shell [TBD]

```
(kb: dev) my-project (master) $ kb shell
Running shell in pod `my-project-...` in kubectl `dev`

root@bcd23f231d09:/#

```

# get completion code

```
(kb: dev) my-project $ kb completion >~/.kyber-completion.sh
(kb: dev) my-project $ source ~/.kyber-completion.sh
(kb: dev) my-project $ kuse <tab>
```

Add `source ~/.kyber-completion.sh` to your shell `.profile`.
