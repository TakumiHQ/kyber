# kyber

kyber is an opinionated kubernetes deployment tool.

# initialize a project

```
(kb: dev) my-project (master) $ kb init
Will associate `my-project` branch `master` with kubectx: `dev`
Correct [Y/n]
Did not find an existing deployment for `my-project` in `dev`:
Create one? [y/N]
... created deployment: my-project in `dev`
...
```


# deploy a project

```
(kb: dev) my-project (master) $ kb deploy [<target environment> [<tag defaults to tip of current branch>]]
...
```
