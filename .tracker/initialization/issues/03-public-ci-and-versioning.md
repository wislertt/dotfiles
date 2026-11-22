# 03: Public CI and versioning

Status: ready-for-agent

Blocked by: None (can start immediately)

Spec: `.tracker/initialization/spec.md`.

**What to build:** Every pull request to the public repo is linted and scanned in CI by the same commands the owner runs locally, titles are checked, and a merge to `main` produces a version and tags. The shape follows the bakefile repo's workflows, without any publish step.

- [ ] A pre-commit and lint workflow runs the tool-manager install, then the repo's `bake lint` (plus pre-commit), on pull requests
- [ ] A security workflow runs a vulnerability scan and a secret scan over history, on push and daily
- [ ] A pull request title check enforces conventional commits
- [ ] A CD workflow runs semantic-release and creates version tags and release notes on `main`, with no publish step
- [ ] Every action is pinned by commit SHA with its version in a trailing comment, and every workflow sets minimal permissions
- [ ] A CI orchestration workflow calls the pieces the way the bakefile repo's does
- [ ] All workflows pass on a pull request for this branch
