# 01: Safe, standalone Apply

Status: ready-for-agent

Blocked by: None (can start immediately)

Spec: `.tracker/initialization/spec.md`. Decision: `docs/adr/0001-private-groups-load-by-environment.md`.

**What to build:** Apply never overwrites an unmanaged file, and the public repo applies on its own. On a machine with existing config, Apply refuses the conflicting regular files, names them, leaves them untouched and exits non-zero. A public clone with no private companion applies its public groups and exits 0. On the owner's machine the private groups still load without any extra step. Apply ends with an Assert, built from bakelib's shared asserts plus one assert that each declared secret resolves. Every use of "preflight" is gone. A repeatable local Fresh-machine check (a throwaway `HOME`) exercises the whole path.

- [x] Apply runs the tool manager's dotfile apply with no force flag and no skip-confirmation flag
- [x] An existing regular file at a target makes Apply exit non-zero, name the file, print how to resolve it (forcing is a manual choice made outside `bake`), and leave the file untouched
- [x] `bake` has no force option
- [x] A second Apply on an applied machine changes nothing and exits 0
- [x] The README states that Apply replaces a symlink that points elsewhere, and only the link changes
- [x] The three private groups move to a private environment config in the public repo root; Apply passes the private environment flag only when the private companion's source directory exists
- [x] A public clone with no `private/` applies the public groups and exits 0 (verified in a throwaway clone)
- [x] A full Apply with `-E private` and the real, complete `private/` links all public and private groups (verified; result recorded in the spec)
- [x] The hand-written check is replaced by bakelib's age-key and bootstrap-secrets asserts plus one repo assert that each declared secret resolves; each failure message says what is missing (no fix hint of our own, decided after review)
- [x] No "preflight" remains in code, docs or wiki, other than the glossary `_Avoid_` line
- [x] A repeatable local check runs the Fresh-machine path (Apply, Apply again, conflict refusal, public-only clone, private loading) in a throwaway `HOME` and asserts only exit codes, link targets and idempotence
- [x] ADR 0001 is committed with the change; `bake lint` passes
