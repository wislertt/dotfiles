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
- **Update** (`bake update`): upgrades tools and, on macOS, Brewfile apps, then prunes the old versions and caches it replaced, on demand.
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

`bake update` upgrades tools and, on macOS, the Brewfile apps, only when you run it, then removes the old versions and caches it replaced (`mise prune`, `uv cache prune` and, on macOS, `brew cleanup`).

`bake apply` links the dotfiles into `~`, then asserts (age key present, Bitwarden token stored, each declared secret resolves). It prints no secret values and writes nothing, but resolving a secret may contact the secret store. If the assert fails, it reports what is missing; on a new machine `bake setup-dev` sets up the age key and token.

The repo root is also linked to `~/.config/bake`, which makes this the global bake: after `bake apply`, `bake <command>` works from any folder without a `bakefile.py`, and `bake -g <command>` reaches it from inside another project. It needs bakefile 0.0.87 or newer (earlier versions fail from a folder that has its own `src/__init__.py`).

`bake tidy` lists Strays: anything installed that no mise config, Brewfile or Keep list accounts for (Homebrew formulas and casks, `uv tool`, `cargo install`, global npm and pnpm packages, dead links on `PATH`, old tool-manager folders, apps, copies of a mise tool elsewhere on `PATH`, unknown files in `~/.local/bin`, Rust toolchains other than `stable`, `beta` and `nightly` that no repo pins). The repos read for `rust-toolchain.toml` and `rust-toolchain` pins are named in `src/lib/tidy.toml`; only repo roots one or two folders down are read. It also covers expired GitHub signing keys and ones that never expire, and every SSH key on the GitHub account (git uses HTTPS). It removes each Stray it can with the manager that owns it, without asking, and lists the rest with the command to run: anything needing sudo, apps, unknown `~/.local/bin` files, copies of a mise tool, signing keys that never expire and GitHub SSH keys. Run `bake tidy --check` first: it lists everything, removes nothing and fails if there are any. To keep a Stray, add `"kind:name" = "reason"` to `src/lib/keep.toml` (or `private/src/lib/keep.toml` if it says who or where). See ADR 0003.

## Conflicts

`bake apply` never overwrites a regular file. If one already exists at a target, Apply names it, leaves it untouched and exits non-zero: move or delete it, then rerun. Forcing (`mise dotfiles apply --force`) is a manual choice made outside `bake`. Apply does replace a symlink that points elsewhere; only the link changes.

## Private companion

With `private/` checked out, Apply also loads the private groups (declared in `private/mise.private.toml`, linked from the repo root; see ADR 0001). Without it the public groups apply on their own.

## Check

`bake test` runs the unit tests. `bake test-integration` runs the real `mise` in a throwaway `HOME`: apply, apply again, conflict refusal, a public-only clone, private loading and overlap rejection.
