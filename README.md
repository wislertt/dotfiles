# dotfiles

Machine setup for my computers, linked with [mise](https://mise.jdx.dev) and driven by `bake`. CI tests the Fresh-machine path on macOS and Linux; the Brewfile apps are macOS-only. Private parts live in the `private/` submodule ([dotfiles-private](https://github.com/wislertt/dotfiles-private)).

## Four homes

Each thing lives in exactly one home.

- **Bitwarden**: secret values only, named `DOTFILES_*`.
- **Public repo**: secret references (names in `fnox.toml`, never values) and config that is the same on every machine and reveals nothing about the owner.
- **Private repo** (the `private/` submodule): anything that reveals an account, employer or work setup, or is personal. Still no secret values.
- **Disposable**: state a machine regenerates and nothing versions (service passwords, OAuth tokens, containers, `.venv`).

## Four times

- **Apply** (`bake apply`): links the dotfiles, then asserts.
- **Setup** (`bake setup-dev`): installs what is missing (mise tools, and on macOS the Brewfile apps), never upgrades mise tools, ends with Apply.
- **Update** (`bake update`): upgrades tools and, on macOS, Brewfile apps, on demand.
- **Use**: not a command. Whenever a linked script or shell start runs.

Terms are in [GLOSSARY.md](GLOSSARY.md), decisions in [docs/adr/](docs/adr/).

## New machine

1. Install [mise](https://mise.jdx.dev).
2. `mise install` (brings `bake`).
3. `bake setup-dev`: installs tools and, on macOS, the apps in `src/lib/Brewfile`, creates the age key, stores the Bitwarden token, then runs `bake apply` as its last step.

The same three commands run in CI as the Fresh-machine job (workflow `test-e2e-fresh-machine`) on macOS and Linux, with throwaway secret values and without the private companion.

## macOS-only

The Brewfile apps (`src/lib/Brewfile`, casks plus mise itself) are installed on macOS and skipped elsewhere. Everything else is meant to be portable.

## Everyday

`bake update` upgrades tools and, on macOS, the Brewfile apps, only when you run it.

`bake apply` links the dotfiles into `~`, then asserts (age key present, Bitwarden token stored, each declared secret resolves). It prints no secret values and writes nothing, but resolving a secret may contact the secret store. If the assert fails, it reports what is missing; on a new machine `bake setup-dev` sets up the age key and token.

The repo root is also linked to `~/.config/bake`, which makes this the global bake: after `bake apply`, `bake <command>` works from any folder without a `bakefile.py`, and `bake -g <command>` reaches it from inside another project. It needs bakefile 0.0.87 or newer (earlier versions fail from a folder that has its own `src/__init__.py`).

`bake duplicates` lists copies of a declared mise tool that sit elsewhere on `PATH` (for example a Homebrew `jq` after `jq` moved to `mise.toml`). It only reports: remove each copy with the package manager that owns it.

## Conflicts

`bake apply` never overwrites a regular file. If one already exists at a target, Apply names it, leaves it untouched and exits non-zero: move or delete it, then rerun. Forcing (`mise dotfiles apply --force`) is a manual choice made outside `bake`. Apply does replace a symlink that points elsewhere; only the link changes.

## Private companion

With `private/` checked out, Apply also loads the private groups (declared in `private/mise.private.toml`, linked from the repo root; see ADR 0001). Without it the public groups apply on their own.

## Check

`bake test` runs the unit tests. `bake test-integration` runs the real `mise` in a throwaway `HOME`: apply, apply again, conflict refusal, a public-only clone, private loading and overlap rejection.
