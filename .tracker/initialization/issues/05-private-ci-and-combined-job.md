# 05: Private CI and combined job

Status: ready-for-agent

Blocked by: 03 (Public CI and versioning), 04 (Public Fresh-machine job and CI secrets)

Spec: `.tracker/initialization/spec.md`.

**What to build:** The private repo is held to the same bar as the public one, and the full path including the private groups is tested where only the owner reads the logs. The private repo gets the same CI set and versioning, using its own bake space. Its Fresh-machine job checks out public at `main`, places private at the private path, and runs the combined path.

- [x] Private has the same workflows as public ticket 03 (lint, security, pull request title check, versioning and tags, orchestration), pinned and with minimal permissions, calling its own bake space (plus a `test.yml`: private now has unit and integration tests; `security.yml` also needs `pull-requests: read` for gitleaks, and `mise.toml` needs `npm:oxfmt`; first release `v0.0.0` tagged at the first commit so zerv has a base)
- [x] A combined Fresh-machine job checks out public at `main` and private at `private/`, runs Setup and Apply twice with the private environment flag and the dummy-secrets profile, on macOS and, if it passes, Linux (`test-e2e-fresh-machine.yml`, same name as public; both OSes green on PR #2; a `public_ref` dispatch input tests private against a public branch; `git config submodule.private.update none` keeps Setup from resetting private; it also runs private's and public's integration tests)
- [x] The combined job runs on pull requests that touch setup-related files and weekly, so a public change that breaks the private groups is caught (path filter, so it is not called from `ci.yml`; the weekly schedule has not fired yet)
- [x] The private groups link and the private Brewfile is applied on macOS in that job (the private Brewfile has no casks yet, so the macOS step applies an empty file)
- [x] The workflows pass on a pull request for this branch ([wislertt/dotfiles-private#2](https://github.com/wislertt/dotfiles-private/pull/2), squash-merged as `a90a449`; it exposed public's deptry scanning `private/tests`, fixed in public as `c00317c` with `extend_exclude = ["private"]`)
