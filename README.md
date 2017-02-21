# kyber

kyber is an opinionated wrapper around ECR-backed kubernetes deployments.

# initialize a project

```
(kb: dev) my-project (master) $ kb init
Did not find an existing deployment for `my-project` in `dev`:
Create one? [y/N]

.. prompt for name, docker (registry), port, external dns?
... created deployment: my-project in `dev`
... created service: my-project
... created secret: my-project-cfg
...
```


# deploy a project

```
(kb: dev) my-project (master) $ kb deploy [<tag defaults to tip of current branch>]
...
```


# configure project environment/secrets

```
(kb: dev) my-project (master) $ kb config [get/set]
```

# see project deployment status

```
(kb: dev) my-project (master) $ kb status
Version: git_d3a4d231ac7f8e91de41.. (3 behind)
Current branch: Deployable (ECR timestamp: ...)
Project: my-project
docker: 12345.dkr.ecr.us-east-1.amazonaws.com/my-project
```

# run a shell

```
(kb: dev) my-project (master) $ kb shell
Running shell in pod `my-project-...` in kubectl `dev`

root@bcd23f231d09:/#

```

# get completion code

```
(kb: dev) my-project $ $(kb completion)
(kb: dev) my-project $ kuse <tab>

```

# Overview

```
kb init -> creates a new deployment + service + secret
kb deploy -> deploys
kb config
   get    ->
   set    ->
kb status ?
kb shell  -> runs /bin/bash in a container
kb ...
```
