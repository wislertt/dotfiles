# 01: Tidy

Status: ready-for-agent

Blocked by: None (can start immediately)

Spec: `.tracker/enhancements/spec.md` (stories 1-21, 44).

**What to build:** `bake tidy --check` lists every Stray on the machine and exits nonzero if there are any, removing nothing. Plain `bake tidy` lists them, asks y/N for each, and removes it with the manager that owns it. Strays on the public or private Keep list are skipped. Tidy absorbs Duplicates.

- [ ] Reports every Stray kind in the spec: Homebrew leaves and casks not in a Brewfile, `uv tool`, `cargo install`, global npm and pnpm packages, dead links in `PATH` directories, missing `PATH` directories, leftover tool-manager folders, apps not in a Brewfile (macOS), copies of declared mise tools (Duplicates' rules carried over), unknown regular files in the local bin folder
- [ ] `--check` removes nothing, exits nonzero with Strays and zero without; not run in CI
- [ ] Plain `tidy` asks per Stray and runs the owning manager's uninstall; Homebrew's autoremove after any Homebrew uninstall; a leftover folder in the home directory is made writable, then removed
- [ ] Anything needing sudo, apps, and unknown local bin files are only named, with the command to run
- [ ] Public and private Keep lists (`kind:name` key, one-line reason) are honoured; the private one is read only when the private companion exists; both seeded from v1 ticket 08's deliberately-undeclared items, work-revealing ones in the private list
- [ ] `bake duplicates` is removed
- [ ] Tested at the command with `FakeCtx` (canned manager outputs, temp home, `PATH` and Keep lists); no test touches the real machine
- [ ] ADR 0003 records Tidy removing per item with Keep lists, reversing v1 ticket 07; GLOSSARY drops Duplicates; README and AGENTS.md updated
- [ ] `bake lint` and `bake test` pass
