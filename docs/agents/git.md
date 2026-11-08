# Git conventions

Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

Scope names the package when the change lives in one package:

```
feat(backend): add venue search endpoint
test(backend): cover dependency state cleanup
fix(frontend): keep focus after pagination
docs(backend): use nil uuid in agent docs
```

Repo-wide changes carry no scope: `ci:`, `build:`, `docs:` (workflows, root
tooling, root docs).

Split a change that touches both packages into one commit per package.

Branch names: `username/my-feature`.
