# 05: Own more config

Status: done

Blocked by: None (can start immediately)

Spec: `.tracker/enhancements/spec.md` (stories 33-37).

**What to build:** Apply owns only the keys we care about in files that apps also rewrite (Claude Code's settings, Zed's settings), and links agent-home's files instead of the owner linking them by hand. Needs a decision first: whether a private dotfile group points at the agent-home checkout, or the files move into dotfiles.

- [x] Decision recorded: where agent-home's files live and which group links them
- [x] Each partly owned file has a public or private decision and a list of owned keys
- [x] Apply merges the owned keys with mise's merge mode and leaves the app's other keys untouched; a rerun changes nothing; the app rewriting the file does not break the next Apply
- [x] Apply links every agent-home file linked by hand today, the hand links are gone, and Apply still works without agent-home
- [x] No mode that writes a secret into a file
- [x] Covered by the throwaway-HOME integration test; `bake lint` and `bake test-integration` pass

## Comments

### Decisions (grilling, 2026-11-25)

Everything goes private for now; what to make public is decided later.

- **agent-home's files:** `user-rules.md` moves into dotfiles at `private/src/home/.claude/rules/user-rules.md`, linked by the existing `private-home` group. agent-home was only a temporary place for it. No new group, so Apply works without agent-home for free. No ADR: moving one file back is cheap.
- **`statusline.sh`:** moves to `private/src/home/.claude/statusline.sh`, linked whole.
- **Merge sources:** an unlinked `private/src/merge/`, laid out like the target path under `~`; entries in `mise.private.toml`. A source inside a linked group root would also be symlinked over the target.
- **`~/.claude/settings.json`:**
    - enforced (`merge = true`, `private/src/merge/.claude/settings.json`): `autoMemoryEnabled`, `disableArtifact`, `disableBundledSkills`, `disableClaudeAiConnectors`, `disableWorkflows`, `skipDangerousModePermissionPrompt`, `statusLine`, `permissions.allow`, `permissions.deny` (arrays are replaced whole);
    - default (`merge = "missing"`, `private/src/merge/.claude/settings.defaults.json`): `model`, `modelSettings`;
    - never owned: `hooks` (Orca writes them).
- **`~/.config/zed/settings.json`:** enforced, `format = "jsonc"`, every key the file has today, source `private/src/merge/.config/zed/settings.json`. Remove the public `src/config/zed/settings.json`.
- **Secret ban:** `bake lint` fails on any `[dotfiles]` entry with `mode = "fnox"` or a template whose source calls `secret(`. Unit tested.
- **Migration:** no code. On this Mac, remove the hand symlinks `~/.claude/rules/user-rules.md` (to agent-home) and `~/.config/zed/settings.json` (to the public source) once, asking the owner first, then `bake apply`. mise refuses a target that links elsewhere and `bake apply` never forces, so another machine gets Apply's existing "move or delete" error.
- **agent-home cleanup:** in its working tree, delete `home/` and update lines 15 and 117 of `wiki/00-gtd/01-action-support/dotfiles/1-raw/design.md` (only those lines; the file has the owner's uncommitted edits). The owner commits agent-home.
- **Tests:** new `private_machine` integration tests (local, skipped in CI): owned keys merge in, an app-added key survives, a changed default survives, a rerun changes nothing, `user-rules.md` and `statusline.sh` are linked. The existing public Apply test covers "works without agent-home".
- **Scope:** Claude Code, Zed and agent-home's links only.
- **Glossary:** "Partly owned file" added.

### Done (2026-11-25)

- Migration ran on this Mac: the two hand symlinks and the regular file `~/.claude/statusline.sh` (Apply refuses to link over it) were removed with the owner's go-ahead, then `bake apply`. `~/.claude/settings.json` came out byte-identical.
- agent-home (uncommitted, for the owner): `home/` deleted, design.md lines 15 and 117 updated, `home/` dropped from `CAPPED` in `bakefile.py`, and the link in `research/agent-memory.md` replaced, so its lint passes.
- The secret ban checks only explicit `mode = "fnox"` and `mode = "template"` entries, as decided. Not covered: an entry relying on `dotfiles.default_mode = "template"`, inline `content`, a dotfile group in template mode, and `[bootstrap.secrets]`.
