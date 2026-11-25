# 02: Tidy

Status: done

Blocked by: 01 (Structure the bake code)

Spec: `.tracker/enhancements/spec.md` (stories 1-21, 44).

**What to build:** `bake tidy --check` lists every Stray on the machine and exits nonzero if there are any, removing nothing. Plain `bake tidy` removes every Stray it can with the manager that owns it, without asking, and lists the rest. Strays on the public or private Keep list are skipped. Tidy absorbs Duplicates.

- [x] Reports every Stray kind in the spec: Homebrew leaves and casks not in a Brewfile, `uv tool`, `cargo install`, global npm and pnpm packages, dead links in `PATH` directories, leftover tool-manager folders, apps not in a Brewfile (macOS), copies of declared mise tools (Duplicates' rules carried over), unknown regular files in the local bin folder, and GitHub signing keys that have expired (removed) or never expire (named); `clean-signing-keys` is removed
- [x] `--check` removes nothing, exits nonzero with Strays and zero without; not run in CI
- [x] Plain `tidy` runs the owning manager's uninstall for each Stray without asking (changed from y/N per Stray on 2026-11-24); Homebrew's autoremove after any Homebrew uninstall; a leftover folder in the home directory is made writable, then removed
- [x] Anything needing sudo, apps, and unknown local bin files are only named, with the command to run
- [x] Public and private Keep lists (`kind:name` key, one-line reason) are honoured; the private one is read only when the private companion exists; both seeded from v1 ticket 08's deliberately-undeclared items, work-revealing ones in the private list
- [x] Tidy is its own command module (with its pure logic in core), and `bake duplicates` is removed with its command and core modules
- [x] Tested at the command with `FakeCtx` (canned manager outputs, temp home, `PATH` and Keep lists); no test touches the real machine
- [x] ADR 0003 records Tidy removing per item with Keep lists, reversing v1 ticket 07; GLOSSARY drops Duplicates; README and AGENTS.md updated
- [x] `bake lint` and `bake test` pass

## Comments

2026-11-24, implementation:

- Homebrew Strays come from `brew bundle cleanup` (no `--force`) run per Brewfile; a Stray is in every listing, and formulas are limited to `brew leaves`. A first draft used `brew leaves` minus Brewfile names, which would have offered a declared cask's formula dependency.
- A copy of a declared mise tool is only named, with no command: the path says which manager owns it.
- Leftover folders checked: asdf, pyenv, nvm, bun, volta, fnm, conda, miniconda3, anaconda3, miniforge3 in home; `/usr/local/go` (sudo, named only). Dead links in system directories (`/usr/bin`, `/bin`, `/usr/sbin`, `/sbin`) are not reported.
- Keep lists: `src/lib/keep.toml` and `private/src/lib/keep.toml`. Ticket 08 recorded no deliberately undeclared items, so the public list starts with only macOS's own (Safari, the cryptex `PATH` entries from `/etc/paths.d/10-cryptex`). Open: the owner sorts the rest of `bake tidy --check` (cargo, local bin files, `/pkg/env/global/bin`, `/usr/local/go`) into removal or a Keep list; apps are ticket 06.

2026-11-24, no prompts: the owner wanted `bake tidy` to need no decisions, so the y/N per Stray is gone. Plain `tidy` removes what it can, `--check` previews, and the Keep list holds anything to keep. GitHub signing-key clean-up moved in from `clean-signing-keys`: expired keys (not this machine's) are deleted, and keys that never expire are only named, since they may have been added by hand. A failed removal is reported, the rest still run, and Tidy exits nonzero. Spec story 4 and ADR 0003 were updated to match.

2026-11-24, output: plain `tidy` prints what it checked, each removal and a one-line summary pointing at `--check`; `--check` lists what plain `tidy` would remove, then what needs the owner, grouped by kind with what to do and the full Keep-list key.

2026-11-24, missing `PATH` directories dropped: the check read the `PATH` of whichever terminal ran bake, so Orca terminals listed a dozen folders Orca adds whether or not they exist. A missing folder is harmless and its fix is editing config, so the kind is gone (spec story 10), with its Keep entries. A zsh fix stops a removed folder cycling back through launchd: `20-tools.zsh` hands launchd only folders that exist.

2026-11-24, closed: the owner sorted `bake tidy --check` on this machine. Removed: the cargo crate, the `/usr/local/bin` dead links, `/usr/local/go` (and its `/etc/paths.d/go`), the unknown `~/.local/bin` files and ZCode. `missing-path` is dropped. The public Keep list holds only `app:Safari`, and no private list is needed yet. The 38 remaining apps are ticket 06.
