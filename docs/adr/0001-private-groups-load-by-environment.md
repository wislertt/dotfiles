# Private groups load through `mise.private.toml`, not the base config

The three private dotfile groups are declared in `mise.private.toml` (public repo root, next to `mise.toml`) and `bake apply` passes `-E private` only when `private/src` exists. In the base `mise.toml`, a public clone without the submodule fails with `sources do not exist` and links nothing, so neither CI nor a stranger could use the public repo alone. The alternatives were keeping the groups in `mise.toml` (breaks the standalone clone) or a generated config (a hidden second source of truth).
