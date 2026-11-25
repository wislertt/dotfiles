# dotfiles

Public dotfiles, linked with mise and driven by `bake`. macOS and Linux are tested in CI (the Fresh-machine job); keep new config portable where it is cheap, and guard anything macOS-only (the Brewfile apps are macOS-only). Rationale: `<vault>/repos/wislertt/agent-home/wiki/00-gtd/01-action-support/dotfiles/1-raw/design.md`. Terms: [GLOSSARY.md](GLOSSARY.md).

## Four homes

Put each thing in exactly one home.

- **Bitwarden**: secret values only, named `DOTFILES_*`. Test: would leaking it cause harm?
- **Public repo**: secret references (names in `fnox.toml`, never values) and config that is the same on every machine and reveals nothing about the owner. Test: could a stranger read it with no loss?
- **Private repo** (the `private/` submodule): anything that reveals an account, employer or work setup, or is personal. Still no secret values. Test: does it say who or where?
- **Disposable**: state a machine regenerates and nothing versions (service passwords, OAuth tokens, containers, `~/.aws/sso/cache`, `.venv`, `.scratch/`). Test: can it be deleted and rebuilt?

## Secrets

- A secret reaches a program at start, as an env var or argument fetched with `bake secret get`.
- Never write a secret into a file we manage. A file a tool owns and writes itself is disposable: leave it alone.

## Bake verbs

- `bake secret refresh` only refreshes the cache.
- A fetch function only fetches.
- `bake apply` only links, then runs the assert (age key present, Bitwarden token stored, each declared secret resolves; no values printed, nothing written; resolving a secret may contact the secret store). On failure it exits nonzero and reports what is missing, without saying how to fix it.
- Anything that starts or changes a service is a script in `src/bin/`.

## Four times

Every new thing is assigned to one of these when it is added, and captured in that step.

- **Apply**: `bake apply`, links dotfiles.
- **Setup**: `bake setup-dev`, installs tools from mise (`mise.toml`) and, on macOS, the casks in `src/lib/Brewfile`, `private/src/lib/Brewfile` and each of this machine's role Brewfiles, then each macOS settings script that changed; mise tools are not upgraded. Includes `bake setup-fnox`, then `bake apply`, then the Signing key (create, renew, publish to GitHub).
- **Update**: `bake update`, on demand. Upgrades tools and, on macOS, Brewfile apps, then prunes what it replaced (`mise prune`, `uv cache prune`, on macOS `brew cleanup`), runs each macOS settings script that changed, then renews and publishes the Signing key.
- **Use**: not a bake command. Whenever something that invokes our dotfiles runs (a linked script, a shell start).

Fresh machine: install mise, `mise install`, `bake setup-dev`. Everyday: `bake apply`.

## Layout and commands

- `src/bin` links to `~/.local/bin`, `src/config` to `~/.config`, `src/home` to `~`. `src/lib` is not linked: scripts and `bake` read it from the repo (shared env files, the Brewfiles, the Keep lists, `tidy.toml` (the repos roots Tidy reads for Rust pins), `sudo-askpass` (bake runs commands without a terminal, so `brew bundle` gets `SUDO_ASKPASS` and a cask's sudo asks in a dialog; casks also run with `--adopt`), and `macos/*.sh`: one settings script per area, run by Setup and Update when its content changes, with a stamp in `~/.local/state/dotfiles/macos/`). Machine list: `private/src/lib/machines.toml` maps a serial number (Linux: `/etc/machine-id`) to `{ name = "...", roles = [...] }`. Setup asks for the name on an unlisted machine and adds it there; anything that needs the name (the Signing key title) gets it from `_machine_name()`, which fails with "run `bake setup-dev`" when there is none (CI sets `DOTFILES_MACHINE_NAME`). A role adds `private/src/lib/Brewfile.<role>` and `keep.<role>.toml` on that machine only; an unlisted machine gets the base files. `bake lint` checks every role Brewfile and that each role in the list has a file.
- `private/src/{bin,config,home}` link to the same targets. `private/src/merge` is not linked: it holds the owned keys of each Partly owned file, laid out like the target under `~`, with a `merge` entry in `mise.private.toml`. `bake lint` fails on any `[dotfiles]` entry that would write a secret (`mode = "fnox"`, or a template that calls `secret(`).
- The repo root itself links to `~/.config/bake` (a `[dotfiles]` entry in `mise.toml`), so this bakefile is the global bake: plain `bake` outside any project uses it, and `bake -g` uses it inside one.
- A new file in an existing group needs nothing. A new target needs a group in `mise.toml` (`[dotfile_groups.*]` and `bootstrap.dotfile_groups`); private groups go in `mise.private.toml`, loaded with `-E private` when `private/` exists.
- Zsh modules are `src/config/zsh/conf.d/NN-name.zsh`, loaded in order: 10 path, 20 tools, 30 aliases, 40 claude. Public modules use 10-49, private modules use 50-89. Pick the next free number in the range that fits.
- `bake lint`: format and lint checks. `bake apply`, `bake setup-dev`, `bake setup-fnox`, `bake update`: as above.
- Bake code: the root `bakefile.py` re-exports `src/python/bakefile.py`, which only composes the command mixins into the bakebook. A new bake command (or bakelib hook family) is a new mixin in `src/python/commands/`, its pure logic (no bakelib import) goes in `src/python/core/`, and the mixin is added to the bakebook. Paths start from `core.repo.ROOT`. Tests mirror the layers in `tests/unit/commands/` and `tests/unit/core/`.
- `bake tidy`: removes every Stray it can with the manager that owns it, without asking (expired GitHub signing keys included, and Rust toolchains other than `stable`, `beta` and `nightly` that no repo under `src/lib/tidy.toml`'s `repos` pins at its root), and names the rest; `--check` removes nothing and fails on any Stray (not run in CI). `--caches` also clears Docker images and build cache (volumes only with `--volumes`) and, on macOS, `mo clean`. Sudo, apps, unknown `~/.local/bin` files, copies of a mise tool, never-expiring signing keys and GitHub SSH keys (git uses HTTPS, so every one is a Stray) are only named. Keep lists: `src/lib/keep.toml`, `private/src/lib/keep.toml` for anything that says who or where, and the role's `private/src/lib/keep.<role>.toml` for what only some machines have. Apply and Setup never remove; Update removes only old versions and caches it replaced (ADR 0003).
- A command-line tool goes in `mise.toml` at `latest`; pin a version there only when a release breaks something, with a one-line comment why. A Python command-line tool needed from any directory goes in `src/config/mise/config.toml` as `"pipx:<name>"` (mise installs it with uv), never with `uv tool install`. A macOS GUI app goes in a Brewfile as a `cask` line, and nowhere else; the only other Brewfile line is `brew "mise"` (the bootstrap). `bake lint` checks both.

## Conduct

- Do not print values from a secret-adjacent file. Check by length or hash, or copy to the clipboard.
- A temporary secret the agent needs (for example a CI token) goes into the gitignored `fnox.local.toml`, age-encrypted, never into `fnox.toml` (a bare `fnox set` writes there). The user stores it from the clipboard (`! pbpaste | fnox -c fnox.local.toml set -p bake-cache-age NAME_TMP`). The agent reads it with `fnox -c fnox.local.toml get NAME_TMP`, never prints it, and removes it when done (`fnox -c fnox.local.toml remove NAME_TMP`).
- Verify before claiming. Run it or read the file.
- Do not delete or stop something because it looks unused. Look at the target and ask.
- Do not name the account or employer behind a private choice in any public file.

## Agent skills

### Issue tracker

Local markdown under `.tracker/` (committed), never `.scratch/`; GitHub Issues on `wislertt/dotfiles` only when I ask for it. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single context: `GLOSSARY.md` and `docs/adr/` at the root. See `docs/agents/domain.md`.
