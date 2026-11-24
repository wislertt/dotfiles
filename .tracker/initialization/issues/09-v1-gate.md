# 09: v1 gate

Status: resolved

Blocked by: 07 (Duplicates report), 08 (Tool decisions)

Spec: `.tracker/initialization/spec.md`.

**What to build:** The final checks before calling v1.

- [x] `mise dotfiles diff` reviewed with no surprises
- [x] A clean secret scan over the full history of the public and private repos
- [x] One real new-machine run of `mise install`, `bake setup-dev` and `bake apply` works
- [x] Each v1 gate item in the spec is ticked off, and the owner confirms v1

## Comments

2026-11-24, agent checks:

- `mise dotfiles diff` and `mise dotfiles diff -E private`: "all files are applied".
- gitleaks 8.30.1, `gitleaks git --log-opts=--all`: public 29 commits, private 13 commits, no leaks; working tree (`gitleaks dir .`) clean too.
- CI: latest `test-e2e-fresh-machine`, `security` and `cd` on public `main` succeeded (2026-11-23); private `main` `cd` and `security` succeeded.
- Spec gate gap: no dependency-update config (no `renovate.json` or `.github/dependabot.yml`), although the spec's v1 gate and CI decision require one.
- Left for the owner: the real new-machine run and confirming v1.

2026-11-24, owner: the real new-machine run is covered by the `test-e2e-fresh-machine` CI job, which verifies each PR; the owner confirmed v1. Resolved.
