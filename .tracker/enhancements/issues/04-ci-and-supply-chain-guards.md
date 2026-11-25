# 04: CI and supply-chain guards

Status: ready-for-agent

Blocked by: None (can start immediately)

Spec: `.tracker/enhancements/spec.md` (stories 28-32, 43).

**What to build:** mise's default 24-hour cooldown on new releases is relied on and recorded, workflows are checked for security issues, and CI fails when shell startup gets slow.

- [x] No `minimum_release_age` setting: mise's 24h default (every backend, and npm/pypi transitive dependencies) is enough; the installed mise is checked to hold back a release under 24 hours old
- [x] ADR 0002 notes the default cooldown next to "latest, no lockfile", and how to exempt one tool
- [x] zizmor runs in `bake lint --slow` (so the pre-commit workflow runs it, with the job's token), in both repos, through a subclass of bakelib's `GitHubActionsTools` (which also brings actionlint and actions-up), marked TODO to move zizmor into bakelib
- [x] Every zizmor finding is fixed, or allowed inline with a one-line reason (`self-repository` is disabled in `.github/zizmor.yml`: actionlint rejects the `$/` syntax)
- [x] A CI step times interactive zsh startup and fails above a loose limit
- [ ] `bake lint` passes; CI green
