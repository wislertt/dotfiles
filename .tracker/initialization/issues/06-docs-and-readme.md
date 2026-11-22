# 06: Docs and README

Status: ready-for-agent

Blocked by: 04 (Public Fresh-machine job and CI secrets), 05 (Private CI and combined job)

Spec: `.tracker/initialization/spec.md`.

**What to build:** A stranger, a contributor and an agent can each find what they need, and every claim in the docs matches what CI proved. The repo has a license, a contributing guide, the tracker and agent docs, and a README that explains the setup.

- [ ] `LICENSE` is Apache-2.0, matching the bakefile repo
- [ ] `CONTRIBUTING.md` links the standards, glossary and decisions and says to run `bake lint` before committing
- [ ] The three agent docs (issue tracker, triage labels, domain) are copied from the bakefile pattern with this repo's name, and the steering file has an "Agent skills" section pointing to them
- [ ] The glossary (Update, Assert, Brewfile, Fresh-machine job) and both ADRs are committed
- [ ] The README covers the four homes, the four times, the Fresh-machine path, what is macOS-only, and what to do on a conflict
- [ ] The steering file and README claim macOS and Linux only if the Linux job passes, otherwise macOS only, with the TODO noted
- [ ] `bake lint` passes
