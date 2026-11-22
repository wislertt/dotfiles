# dotfiles

Machine setup for my computers, tested only on macOS. Private parts live in the `private/` submodule ([dotfiles-private](https://github.com/wislertt/dotfiles-private)).

## New machine

1. Install [mise](https://mise.jdx.dev).
2. `mise install` (brings `bake`).
3. `bake setup-dev`: installs tools, creates the age key, stores the Bitwarden token, then runs `bake apply` as its last step.

## Everyday

`bake apply` links the dotfiles into `~`, then runs a preflight (age key present, Bitwarden token stored, each declared secret resolves). It prints no secret values and writes nothing, but resolving a secret may contact the secret store. If the preflight fails, run `bake setup-dev`.
