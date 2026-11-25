# 01: Structure the bake code

Status: resolved

Blocked by: None (can start immediately)

Spec: `.tracker/enhancements/spec.md` (stories 45-53).

**What to build:** All of the bake code is laid out so new features slot in without growing one class, and every bake command behaves exactly as before. The bakebook only composes mixins: one per bake command or bakelib hook family in a commands layer, with pure logic (no bakelib import) in a core layer. Later tickets (Tidy, Machine hygiene) then add their own command modules.

- [x] The bakebook module holds only the bakebook class composing the command mixins, and the bakebook object; the root shim bake reads is unchanged
- [x] The repo root is one constant, replacing every lookup by parent-directory count
- [x] Commands layer, one mixin each: Apply (with its assert), the Setup and Update overrides (tools, Brewfile steps, required tools), lint (shell, Brewfiles, global fnox), secrets (fetch functions and secret key names), duplicates, and the signing clean-up command
- [x] Core layer, no bakelib imports: Brewfiles (paths, line check), signing (moved), duplicates (moved), shell-file classification; named core, not lib, because the repo's lib folder already means unlinked repo files
- [x] No behaviour change: same commands, options, output and exit codes; any fix found along the way is listed for the owner, not made
- [x] Tests mirror the layers (commands and core); existing tests pass with only import and location changes; `FakeCtx` stays shared; no new seam
- [x] The steering file's layout section and the contributing guide say: a new command is a new command mixin, its pure logic goes in core, and it is added to the bakebook; no ADR
- [x] The private companion's bakefile is untouched
- [x] `bake lint` and `bake test` pass

## Comments

- Done. Help output for every command is unchanged and the class order puts the mixins ahead of bakelib's classes, in bakelib's old order. No behaviour fixes were found. Possible follow-ups for the owner: `core/signing.py` still imports `bake` and `typer` (it was moved as is), the `SetupUpdateMixin` calls `_apply` from `ApplyMixin` through a type-checking stub, and the PATH ignore rules for Duplicates stay in the command until Tidy replaces it.
