# dotfiles

Machine setup for my computers, tested only on macOS. Private parts live in the `private/` submodule ([dotfiles-private](https://github.com/wislertt/dotfiles-private)).

## New machine

1. Install [mise](https://mise.jdx.dev).
2. `mise install` (brings `bake`).
3. `bake setup-dev`: installs tools, creates the age key, stores the Bitwarden token, then runs `bake apply` as its last step.

## Everyday

`bake apply` links the dotfiles into `~`, then asserts (age key present, Bitwarden token stored, each declared secret resolves). It prints no secret values and writes nothing, but resolving a secret may contact the secret store. If the assert fails, it reports what is missing; on a new machine `bake setup-dev` sets up the age key and token.

## Conflicts

`bake apply` never overwrites a regular file. If one already exists at a target, Apply names it, leaves it untouched and exits non-zero: move or delete it, then rerun. Forcing (`mise dotfiles apply --force`) is a manual choice made outside `bake`. Apply does replace a symlink that points elsewhere; only the link changes.

## Private companion

With `private/` checked out, Apply also loads the private groups (declared in `private/mise.private.toml`, linked from the repo root; see ADR 0001). Without it the public groups apply on their own.

## Check

`bake test` runs the unit tests. `bake test-integration` runs the real `mise` in a throwaway `HOME`: apply, apply again, conflict refusal, a public-only clone, private loading and overlap rejection.
