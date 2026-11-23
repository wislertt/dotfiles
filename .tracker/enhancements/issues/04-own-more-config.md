# 04: Own more config

Status: ready-for-human

Blocked by: None (can start immediately)

Spec: `.tracker/enhancements/spec.md` (stories 33-37).

**What to build:** Apply owns only the keys we care about in files that apps also rewrite (Claude Code's settings, Zed's settings), and links agent-home's files instead of the owner linking them by hand. Needs a decision first: whether a private dotfile group points at the agent-home checkout, or the files move into dotfiles.

- [ ] Decision recorded: where agent-home's files live and which group links them
- [ ] Each partly owned file has a public or private decision and a list of owned keys
- [ ] Apply merges the owned keys with mise's merge mode and leaves the app's other keys untouched; a rerun changes nothing; the app rewriting the file does not break the next Apply
- [ ] Apply links every agent-home file linked by hand today, the hand links are gone, and Apply still works without agent-home
- [ ] No mode that writes a secret into a file
- [ ] Covered by the throwaway-HOME integration test; `bake lint` and `bake test-integration` pass
