# 04: CI and supply-chain guards

Status: ready-for-agent

Blocked by: None (can start immediately)

Spec: `.tracker/enhancements/spec.md` (stories 28-32, 43).

**What to build:** A new `latest` release waits a week before mise installs it, workflows are checked for security issues, and CI fails when shell startup gets slow.

- [ ] mise's minimum release age is 7 days in the repo and global mise configs, with a one-line comment why; setting name and per-tool exclusion checked against the mise security docs first; ADR 0002 notes it next to "latest, no lockfile"
- [ ] `mise install` and `bake update` still succeed with the cooldown
- [ ] zizmor runs as a pre-commit hook, so `bake lint` and CI run it, in both repos
- [ ] Every zizmor finding is fixed, or allowed inline with a one-line reason
- [ ] A CI step times interactive zsh startup and fails above a loose limit
- [ ] `bake lint` passes; CI green
