# 07: Protect private work in progress

Status: resolved

Blocked by: None (can start immediately)

Spec: `.tracker/enhancements/spec.md` (stories 54-56).

**What to build:** Setup and Update no longer strand work in the private companion. Before the submodule sync, `private/` is checked for work in progress; if there is any, the sync is skipped with a warning and the run continues. Git status and diff show what a submodule bump brings in.

- [x] The sync is skipped, with a warning naming the reason, when `private/` has uncommitted changes, a branch other than main checked out, or commits not on origin/main
- [x] The sync runs as before when `private/` is clean on main, or is not checked out
- [x] The check only reads; it never stashes, commits or switches branches
- [x] Tested with `FakeCtx`: one case per reason skips, a clean main and a missing checkout sync, and an unreachable private companion is still not fatal
- [x] The linked git config sets `status.submoduleSummary = true` and `diff.submodule = log`

Landed ahead of 01, in the current bakebook; 01 moves it with the Setup and Update overrides.
