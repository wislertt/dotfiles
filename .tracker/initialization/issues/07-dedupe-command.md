# 07: Dedupe command

Status: ready-for-agent

Blocked by: 06 (Docs and README)

Spec: `.tracker/initialization/spec.md`.

**What to build:** A `bake dedupe` command removes installs that a declared tool has replaced, so moving a tool from Homebrew (or another global install) to mise or a Brewfile leaves one copy. It is separate from `bake clean` (files in the repo) and is never part of Apply, Setup or Update. It lists duplicates and removes nothing unless run with `--yes`.

A duplicate is an install by brew, `npm -g`, pipx, cargo or `go install` of something that is also declared in `mise.toml` or a Brewfile, and whose replacement is actually installed, not only declared. Anything merely undeclared is never touched, so hand-installed apps stay. Removal goes through the owning manager. Where names differ between managers, an explicit map in the repo decides.

- [ ] Run without `--yes`, it prints each duplicate and the manager that would remove it, changes nothing, and exits 0
- [ ] Run with `--yes`, it removes each listed duplicate through its manager, and an immediate second dry run lists nothing
- [ ] A tool declared but not yet installed (the replacement missing) is not listed
- [ ] An undeclared install is never listed
- [ ] A copy another package still depends on is reported and skipped, not forced
- [ ] Covers brew formulae and casks, `npm -g`, pipx, cargo and `go install`; the name map holds the known differences
- [ ] Tested through a fake package manager, observing only what is listed, removed and the exit code
- [ ] Glossary names Dedupe; ADR 0002 notes that Setup and Update still never remove and Dedupe is the only removal path; the spec's out-of-scope line is narrowed; README and steering file list the command
- [ ] `bake lint` passes
