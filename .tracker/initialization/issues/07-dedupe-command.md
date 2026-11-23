# 07: Dedupe command

Status: ready-for-agent

Blocked by: 06 (Docs and README)

Spec: `.tracker/initialization/spec.md` (story 49).

**What to build:** `bake dedupe` removes an install that a declared tool has replaced, so moving a tool from Homebrew (or another global install) to mise or a Brewfile leaves one copy. It lists duplicates and removes nothing unless run with `--yes`.

## Rules

- A **duplicate** is an install by brew (formula or cask), `npm -g`, pipx, cargo or `go install` of something that is also declared, and whose replacement is actually installed, not only declared.
- Anything merely undeclared is never listed, so hand-installed apps stay.
- Removal goes through the owning manager, never `rm`.
- It is a separate command from `bake clean` (files in the repo) and is never run by Apply, Setup or Update. Those three stay non-destructive (ADR 0002).
- Intended order per tool: declare it, run `bake setup-dev` to install the new copy, run `bake dedupe` to review, run `bake dedupe --yes` to remove.

## Design

- **Declared:** the `[tools]` keys in `mise.toml`, plus `mise.private.toml` when present, plus the `cask` lines of both Brewfiles. A backend prefix is dropped for comparison: `npm:oxfmt` matches the global npm package `oxfmt`, `pipx:bakefile` matches the pipx package `bakefile`.
- **Replacement installed:** for a mise tool, `mise where <tool>` succeeds. For a cask, it appears in `brew list --cask`.
- **Name map:** an explicit map in the repo for names that differ between managers; everything else compares by identical name.
- **Dependencies:** a copy another package still needs is reported and skipped, never forced.
- **Shape:** a new module with one adapter per manager (`installed()` lists names, `uninstall(name)` removes one) and a core that takes the adapters, the declared set and the replacement check. `MyBakebook` gets a thin `dedupe(yes: bool = False)` command that wires them.

## Seams (TDD)

1. **Core rules with fake adapters.** Catches the rules above. Misses whether the real commands are right.
2. **Each adapter through `FakeCtx`** (records commands, runs none). Catches the right list and uninstall command and parsing of one real recorded output sample per manager. Misses later output-format drift.
3. **The `bake dedupe` command.** Catches that `--yes` reaches the core and the exit code. Thin.

No test touches a real package manager: a clean CI runner has no duplicates, and a real removal would change the owner's machine.

## Acceptance criteria

- [x] Without `--yes`, it prints each duplicate and the manager that would remove it, changes nothing, and exits 0
- [x] With `--yes`, it removes each listed duplicate through its manager, and an immediate second dry run lists nothing
- [x] A tool declared but not yet installed (replacement missing) is not listed
- [x] An undeclared install is never listed
- [x] A copy another package depends on is reported and skipped, not forced
- [x] Covers brew formulae and casks, `npm -g`, pipx, cargo and `go install`, with the name map holding the known differences
- [x] Tested at the three seams above
- [x] Glossary names Dedupe; ADR 0002 notes that Setup and Update still never remove and Dedupe is the only removal path; README and steering file list the command
- [x] `bake lint` passes
