# 03: Machine hygiene

Status: resolved

Blocked by: 01 (Structure the bake code)

Spec: `.tracker/enhancements/spec.md` (stories 22-27).

**What to build:** `bake update` drops the old versions and caches it replaced, and dead `PATH` entries stop surviving from shell to shell through the `PATH` saved for GUI apps.

- [x] After upgrading, `bake update` runs mise's prune, uv's cache prune and, on macOS only, Homebrew's cleanup; tested with `FakeCtx`
- [x] Setup and Apply still remove nothing; GLOSSARY's Update entry and the AGENTS.md rule read "Apply and Setup never remove; Update removes only old versions and caches it replaced"
- [x] The `PATH` saved for GUI apps is built fresh (or the step dropped): after one fresh login it holds no entry a fresh login shell would not add, verified by hand
- [x] Zed and Orca, launched from the GUI, still find mise tools
- [x] The launchctl step stays macOS-only and guarded
- [x] `bake lint` and `bake test` pass

## Comments

2026-11-24, implementation: Update's prune is `mise prune --yes` (bake runs it without a terminal) and `uv cache prune` after bakelib's tool upgrades, and `brew cleanup` after the Brewfile upgrades on macOS when Homebrew is installed. Kept out of bakelib's BaseSpace: `mise prune` deletes machine-wide, which a project's `bake update` should not do. The launchctl step builds the GUI `PATH` in the background from a clean login shell (`env -i ... zsh -lc`), keeping only folders that exist, so nothing the current shell inherited can cycle back. Only `.zshrc` modules' additions no longer reach GUI apps; mise tools reach them through the shims folder.

2026-11-24, verified by hand: after a fresh login, `launchctl getenv PATH` held only what a clean login shell adds (local bin, mise shims, Homebrew, the `/etc/paths` folders, `~/.cargo/bin`); the stale mise install folders and `~/Library/pnpm` were gone. Zed and Orca launched from the GUI still find mise tools.
