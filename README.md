# kyber

Kyber is a kubernetes app deployment and management tool.  It's built to easily
create and deploy apps to a kubernetes cluster running in AWS, the apps are
stateless and based on a single docker which can be pulled from an ECR (Elastic
Container Registry).  Additionally kyber sets metadata which will trigger
automatic route53 DNS entries if the [route53-kubernetes](https://github.com/wearemolecule/route53-kubernetes)
plugin is installed.

## Installation

    $ pip install kyber-k8s

## Description

Kyber is tightly coupled with your local kubectl configuration, and the bash/zsh
completion adds a prefix to `$PS1` (shell prompt) so that the currently chosen
kubectl context and the namespace of that context can be seen at all times.  See
details at [completion](#completion).  Also kyber is tightly coupled with git,
and assumes containers are tagged with `git_<hash>` from the local repo.

An "app" consists of the following k8s objects:
 - [Deployment](https://kubernetes.io/docs/user-guide/deployments/)
 - [Service](https://kubernetes.io/docs/user-guide/services/)
 - [Secret](https://kubernetes.io/docs/user-guide/secrets/)

Each of which has the name of the "app".  The `deploy` command constructs a new
image path for `container[0]` of the Deployment, but other parts of the spe
template should be left alone and can be edited with `kubectl edit deployment
{app name}`, for example the number of replicas, and various k8s strategies.

When setting up a new app you need to provide the following metadata:

 - docker base path (`registry/repo` - not including a `:tag`)
 - name (must be unique within this kubernetes cluster namespace)
 - port
 - DNS name (only has effect if [route53-kubernetes](https://github.com/wearemolecule/route53-kubernetes) is installed)
 - SSL certificate ARN

When initializing a new app `kyber` will assume it is health checked using HTTP
GET calls to `/status` on the previously mentioned app port.  The health checks
can be changed/disabled with `kubectl edit deployment {app name}`.

## Kyber Commands

- [init](#init) - initialize a project
- [deploy](#deploy)
- [logs](#logs)
- [config](#config)
  - [list](#list)
  - [get](#get)
  - [set](#set)
  - [unset](#unset)
  - [envdir](#envdir)
  - [load](#load)
- [status](#status)
- [shell](#shell)
- [completion](#completion)
- [dash](#dash)

## init

### Initialize a project

    (kb: dev) my-project $ kb init

Init checks to see if you have a local (copied) `.kyber/config` file which it
can use to initialize the project against this kubernetes context, if a matching
deployment/service/secret trifecta is not found within the context.

Init also checks to see if a trifecta matching the project name exists, and
will attempt to write a `.kyber/config` file to match, if found.  This logic is
a bit too clever and confusing, and should be cleaned up; it was written to
make it easier to setup kyber for an existing project.

If nothing is found, init will prompt for the necessary metadata and then proceed
to create the Deployment, Service and Secret objects as well as the `.kyber/config`
file entry.

## deploy

### Deploy another container to a project

    (kb: dev) my-project $ kb deploy [<tag defaults to tip of current branch>]
    ...


## logs

### Get pod logs

Streams logs from one or all of the pods in the current kyber app. Does not support
all the parameters offered by `kubectl logs`, only `-s/--since-seconds` and
`-f/--follow` are supported.

Also adds a `-k/--keep-timestamps` option to show the ISO-8601 timestamps provided
by k8s and used to order the logs.

    (kb: dev) my-project $ kb logs -k -f
    my-project-875882650-c4wmp: 2017-04-25T14:00:01 ...
    my-project-875882650-dt2cp: 2017-04-25T14:00:02 ...
    my-project-875882650-c4wmp: 2017-04-25T14:00:03 ...
    my-project-875882650-dt2cp: 2017-04-25T14:00:04 ...

## config

The config command group manages the variables defined in the app secret, which is by
default mounted to `/secrets/` within the app container.  The subcommands make it easy
to dump/load the data to/from envdir's and dotenv files, as well as getting, setting
and unsetting individual values.

### list

    (kb: dev) my-project $ kb config list
    SOME=variables
    ARE=more
    EQUAL=than
    OTHERS=100

### get

    (kb: dev) my-project $ kb config get<TAB>
    ARE SOME EQUAL OTHERS
    (kb: dev) my-project $ kb config get ARE
    more

### set

    (kb: dev) my-project $ kb config set OTHERS 99%
    (kb: dev) my-project $ kb config get OTHERS
    99%

### unset

    (kb: dev) my-project $ kb config unset OTHERS
    Do you wish to delete config variable my-project.OTHERS with value of `99%` [y/N]:
    (kb: dev) my-project $ kb config get OTHERS
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

## status

See the current kyber status of a project, most importantly the deployed tag,
the docker registry/repo, and whether the tip of the current master is deployable
(is there a docker named `{app.docker:git_{git.head()}}` in the ECR.

    (kb: dev) my-project $ kb status
    Project: my-project
    Docker: 12345.dkr.ecr.us-east-1.amazonaws.com/takumi-server
    Deployed tag: git_6eea5482b7f55823f86a63d9ddf6d84ec6769a78
    Current tag: git_6eea5482b7f55823f86a63d9ddf6d84ec6769a78 [deployable: y]

## shell

Execute `/bin/bash` inside one of the pods in your app, useful for debugging.
Will choose the first ready pod, or the last one returned if none are ready.
Ready here refers to the kubernetes definition (liveness/readiness).

    (kb: dev) my-project $ kb shell
    Running shell in pod `my-project-...` in kubectx `dev`
    root@bcd23f231d09:~#

## dash

Opens up the kubernetes-dashboard on the service object for the kyber app
in the current context, or if called from outside a kyber context, it will
open the pods dashboard for the current kubectl context.

    (kb: dev) my-project $ kb dash
    Opening dashboard for `my-project` in `dev`

    (kb: dev) ~ $ kb dash
    Not in a kyber context, showing dash for k8s pods in `dev`


`dash` tries to use the command line program `open` which works on OS X, but
on most linux distributions this will probably fail (`xdg-open` might be an
alternative to look for and try).  If dash fails to find the `open` executable
it will report back and print out the URL:

    (kb: dev) my-project $ kb dash
    Unable to launch dashboard automatically (Can't find 'open' executable, is it in your $PATH?)
    URL: https://admin:***@api.kube-dev.you.org/api/v1/proxy/namespaces/kube-system/services/kubernetes-dashboard/#/service/dev/my-project?namespace=dev

## completion

As mentioned above kyber is tightly coupled with the local kubectl config
and context, and thus changes `$PS1` to prefix with your current kubectl
context.  This prefixing can be turned on or off by calling `kubify` and
`unkubify` functions which are declared in the completion script.

    (kb: dev) my-project $ kb completion >~/.kyber-completion.sh
    (kb: dev) my-project $ source ~/.kyber-completion.sh
    (kb: dev) my-project $ kuse <tab>

To install the kyber completion script add `source ~/.kyber-completion.sh` to
your shell `.profile`.

The completion script adds basic tab-completion for the commands of kyber,
but also adds two new commands to more easily switch between kubectl contexts:

### kuse

`kuse` switches between kubernetes contexts, and tab completes as well. It
is basically an alias for `kubectl config use-context`.

    (kb: dev) my-project $ kuse prod
    (kb: prod) my-project $

### kubes

`kubes` lists your kubectl contexts, it's basically an alias for
`kubectl config get-contexts`.

    (kb: dev) my-project $ kubes
    CURRENT   NAME                               CLUSTER                            AUTHINFO                       NAMESPACE
    *         eu-west-1.kube.takumi.com          eu-west-1.kube.takumi.com          eu-west-1.kube.takumi.com      prod
              eu-central-1.kube.takumi.com       eu-central-1.kube.takumi.com       eu-central-1.kube.takumi.com
              eu-central-1.kube.takumi.com-OLD   eu-central-1.kube.takumi.com-OLD   aws_k8s                        dev
