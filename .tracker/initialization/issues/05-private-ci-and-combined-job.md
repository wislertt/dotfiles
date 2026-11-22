# 05: Private CI and combined job

Status: ready-for-agent

Blocked by: 03 (Public CI and versioning), 04 (Public Fresh-machine job and CI secrets)

Spec: `.tracker/initialization/spec.md`.

**What to build:** The private repo is held to the same bar as the public one, and the full path including the private groups is tested where only the owner reads the logs. The private repo gets the same CI set and versioning, using its own bake space. Its Fresh-machine job checks out public at `main`, places private at the private path, and runs the combined path.

- [ ] Private has the same workflows as public ticket 03 (lint, security, pull request title check, versioning and tags, orchestration), pinned and with minimal permissions, calling its own bake space
- [ ] A combined Fresh-machine job checks out public at `main` and private at `private/`, runs Setup and Apply twice with the private environment flag and the dummy-secrets profile, on macOS and, if it passes, Linux
- [ ] The combined job runs on pull requests that touch setup-related files and weekly, so a public change that breaks the private groups is caught
- [ ] The private groups link and the private Brewfile is applied on macOS in that job
- [ ] The workflows pass on a pull request for this branch
