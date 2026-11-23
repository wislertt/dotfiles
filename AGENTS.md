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
- **Setup**: `bake setup-dev`, installs tools from mise (`mise.toml`) and, on macOS, the casks in `src/lib/Brewfile` and `private/src/lib/Brewfile`; mise tools are not upgraded. For now bakelib also upgrades Homebrew here (TODO: drop once nothing in Homebrew is installed by hand). Includes `bake setup-fnox`, and ends with `bake apply`.
- **Update**: `bake update`, on demand. Upgrades tools and, on macOS, Brewfile apps.
- **Use**: not a bake command. Whenever something that invokes our dotfiles runs (a linked script, a shell start).

Fresh machine: install mise, `mise install`, `bake setup-dev`. Everyday: `bake apply`.

## Layout and commands

- `src/bin` links to `~/.local/bin`, `src/config` to `~/.config`, `src/home` to `~`. `src/lib` is not linked: scripts and `bake` read it from the repo (shared env files, the Brewfiles).
- `private/src/{bin,config,home}` link to the same targets.
- The repo root itself links to `~/.config/bake` (a `[dotfiles]` entry in `mise.toml`), so this bakefile is the global bake: plain `bake` outside any project uses it, and `bake -g` uses it inside one.
- A new file in an existing group needs nothing. A new target needs a group in `mise.toml` (`[dotfile_groups.*]` and `bootstrap.dotfile_groups`); private groups go in `mise.private.toml`, loaded with `-E private` when `private/` exists.
- Zsh modules are `src/config/zsh/conf.d/NN-name.zsh`, loaded in order: 10 path, 20 tools, 30 aliases, 40 claude. Public modules use 10-49, private modules use 50-89. Pick the next free number in the range that fits.
- `bake lint`: format and lint checks. `bake apply`, `bake setup-dev`, `bake setup-fnox`, `bake update`: as above.
- `bake duplicates`: read-only report of copies of a declared mise tool elsewhere on `PATH`. It removes nothing; Apply, Setup and Update never remove either.
- A command-line tool goes in `mise.toml` at `latest`; pin a version there only when a release breaks something, with a one-line comment why. A macOS GUI app goes in a Brewfile as a `cask` line, and nowhere else; `bake lint` checks both.

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
