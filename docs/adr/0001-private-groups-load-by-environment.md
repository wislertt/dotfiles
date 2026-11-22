# Private groups load by environment, declared in the private repo

The three private dotfile groups are declared in `private/mise.private.toml`. The public repo tracks only a symlink to it, `mise.private.toml` at its root, and `bake apply` passes `-E private` only when `private/src` exists. The group names and paths therefore never appear in the public repo. In the base `mise.toml`, a public clone without the submodule fails with `sources do not exist` and links nothing, so neither CI nor a stranger could use the public repo alone. With the symlink, a clone without `private/` has a dangling link that mise never reads, because the environment is not selected.

Roots in that file are written `private/src/...`: mise resolves them from the public repo root, not from where the symlink points. The file also lists the public groups in `bootstrap.dotfile_groups`, because it replaces the base list instead of merging with it.

Alternatives rejected:

- Groups in `mise.toml`: breaks the standalone public clone.
- A generated config: a hidden second source of truth.
- `mise.private.toml` as a real file in the public repo: reveals private group names.
- A second `mise -C private` run: mise no longer sees both groups together, so two groups claiming one target are not rejected; the last apply silently wins, because mise treats a symlink pointing elsewhere as replaceable.
