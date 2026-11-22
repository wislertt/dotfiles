# dotfiles

Public dotfiles, linked with mise and driven by `bake`. macOS is the only tested platform; keep new config portable where it is cheap, and guard anything macOS-only. Rationale: `<vault>/repos/wislertt/agent-home/wiki/00-gtd/01-action-support/dotfiles/1-raw/design.md`. Terms: [GLOSSARY.md](GLOSSARY.md).

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

## Three times

Every new thing is assigned to one of these when it is added, and captured in that step.

- **Apply**: `bake apply`, links dotfiles.
- **Setup**: `bake setup-dev`, installs tools, includes `bake setup-fnox`, and ends with `bake apply`.
- **Use**: not a bake command. Whenever something that invokes our dotfiles runs (a linked script, a shell start).

Fresh machine: install mise, `mise install`, `bake setup-dev`. Everyday: `bake apply`.

## Layout and commands

- `src/bin` links to `~/.local/bin`, `src/config` to `~/.config`, `src/home` to `~`. `src/lib` is not linked: scripts read it from the repo.
- `private/src/{bin,config,home}` link to the same targets.
- A new file in an existing group needs nothing. A new target needs a group in `mise.toml` (`[dotfile_groups.*]` and `bootstrap.dotfile_groups`); private groups go in `mise.private.toml`, loaded with `-E private` when `private/` exists.
- Zsh modules are `src/config/zsh/conf.d/NN-name.zsh`, loaded in order: 10 path, 20 tools, 30 aliases, 40 claude. Public modules use 10-49, private modules use 50-89. Pick the next free number in the range that fits.
- `bake lint`: format and lint checks. `bake apply`, `bake setup-dev`, `bake setup-fnox`: as above.

## Conduct

- Do not print values from a secret-adjacent file. Check by length or hash, or copy to the clipboard.
- Verify before claiming. Run it or read the file.
- Do not delete or stop something because it looks unused. Look at the target and ask.
- Do not name the account or employer behind a private choice in any public file.
