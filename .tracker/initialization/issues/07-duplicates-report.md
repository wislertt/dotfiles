# 07: Duplicates report

Status: ready-for-agent

Blocked by: 06 (Docs and README)

Spec: `.tracker/initialization/spec.md` (story 49).

**What to build:** `bake duplicates` reports copies of a declared mise tool that sit elsewhere on `PATH`, so moving a tool from Homebrew (or any other install) to mise shows what is left behind. It is read-only. The owner removes each copy by hand with the package manager that owns it; the path says which.

The first design uninstalled through each package manager (brew, npm, pipx, cargo, go). It was dropped as too much to maintain for a job done once per tool: detecting by `PATH` needs no per-manager knowledge. The ADR 0002 note records this.

## Rules

- A copy is an executable on `PATH` with the same name as one the mise copy ships, outside that tool's own folders.
- A declared tool that mise has not installed yet is not reported.
- System directories, mise shims and project virtualenvs (`.venv/bin`) are not reported. A copy on `PATH` twice is reported once.
- It changes nothing, and Apply, Setup and Update never remove anything either.

## Design

- Declared: the `[tools]` keys of `mise.toml` and `mise.private.toml`, in the form `mise bin-paths` takes (for example `npm:oxfmt`).
- A tool's binaries: the executables in the folders `mise bin-paths <key>` prints.
- Pure function `other_copies(tool_bins, path, ignore)`, tested with temp directories; a thin `duplicates` command reads `PATH` and runs `mise bin-paths`.

## Acceptance criteria

- [x] Lists a copy outside mise, one line per copy as `tool: path`, and removes nothing
- [x] A tool's own folder, mise shims, system directories and project virtualenvs are not reported
- [x] A tool mise has not installed is not reported
- [x] Reports a copy by any manager, including a symlink such as Homebrew's
- [x] Tested through the pure function and the command with `FakeCtx`
- [x] Glossary names Duplicates; ADR 0002 records the choice; README and steering file list the command
- [x] `bake lint` passes
