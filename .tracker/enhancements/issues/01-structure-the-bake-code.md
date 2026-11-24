# 01: Structure the bake code

Status: ready-for-agent

Blocked by: None (can start immediately)

Spec: `.tracker/enhancements/spec.md` (stories 45-53).

**What to build:** All of the bake code is laid out so new features slot in without growing one class, and every bake command behaves exactly as before. The bakebook only composes mixins: one per bake command or bakelib hook family in a commands layer, with pure logic (no bakelib import) in a core layer. Later tickets (Tidy, Machine hygiene) then add their own command modules.

- [ ] The bakebook module holds only the bakebook class composing the command mixins, and the bakebook object; the root shim bake reads is unchanged
- [ ] The repo root is one constant, replacing every lookup by parent-directory count
- [ ] Commands layer, one mixin each: Apply (with its assert), the Setup and Update overrides (tools, Brewfile steps, required tools), lint (shell, Brewfiles, global fnox), secrets (fetch functions and secret key names), duplicates, and the signing clean-up command
- [ ] Core layer, no bakelib imports: Brewfiles (paths, line check), signing (moved), duplicates (moved), shell-file classification; named core, not lib, because the repo's lib folder already means unlinked repo files
- [ ] No behaviour change: same commands, options, output and exit codes; any fix found along the way is listed for the owner, not made
- [ ] Tests mirror the layers (commands and core); existing tests pass with only import and location changes; `FakeCtx` stays shared; no new seam
- [ ] The steering file's layout section and the contributing guide say: a new command is a new command mixin, its pure logic goes in core, and it is added to the bakebook; no ADR
- [ ] The private companion's bakefile is untouched
- [ ] `bake lint` and `bake test` pass
