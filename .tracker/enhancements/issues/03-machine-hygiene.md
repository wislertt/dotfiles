# 03: Machine hygiene

Status: ready-for-agent

Blocked by: 01 (Structure the bake code)

Spec: `.tracker/enhancements/spec.md` (stories 22-27).

**What to build:** `bake update` drops the old versions and caches it replaced, and dead `PATH` entries stop surviving from shell to shell through the `PATH` saved for GUI apps.

- [ ] After upgrading, `bake update` runs mise's prune, uv's cache prune and, on macOS only, Homebrew's cleanup; tested with `FakeCtx`
- [ ] Setup and Apply still remove nothing; GLOSSARY's Update entry and the AGENTS.md rule read "Apply and Setup never remove; Update removes only old versions and caches it replaced"
- [ ] The `PATH` saved for GUI apps is built fresh (or the step dropped): after one fresh login it holds no entry a fresh login shell would not add, verified by hand
- [ ] Zed and Orca, launched from the GUI, still find mise tools
- [ ] The launchctl step stays macOS-only and guarded
- [ ] `bake lint` and `bake test` pass
