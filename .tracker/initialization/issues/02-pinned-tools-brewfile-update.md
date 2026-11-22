# 02: Tools, Brewfile and Update

Status: ready-for-agent

Blocked by: 01 (Safe, standalone Apply)

Spec: `.tracker/initialization/spec.md`. Decision: `docs/adr/0002-mise-for-tools-brew-for-mac-apps.md`.

**What to build:** Two machines get the same tools, macOS apps come from a Brewfile, and upgrades are a deliberate step. Every command-line tool is installed by the tool manager, at `latest` unless a release breaks it (then that one tool is pinned by hand). macOS GUI apps come from a public Brewfile and a private Brewfile, applied by Setup on macOS only. Setup installs only what is missing. A new Update ritual upgrades tools and apps on demand.

- [x] Tools in the tool manager's config use `latest`; a tool is pinned by hand, with a comment why, only when a release breaks it (decided: no `mise.lock`, no Renovate for tools)
- [x] A public Brewfile holds apps that reveal nothing about the owner; a private Brewfile in the private companion holds the rest; both hold casks only, and no tool is in both the tool manager and a Brewfile
- [x] Setup runs the Brewfile step only on macOS; elsewhere Setup runs the tool manager step alone
- [x] The Brewfile step writes no lock file and removes nothing itself (bakelib's Homebrew upgrade and cleanup run too, until nothing is installed by hand)
- [ ] Verified once by hand: apps already installed by hand (Orca, Zed, Docker) are adopted, not reinstalled or broken
- [x] First checks whether bakelib already offers an Update command; reuses it if it does, otherwise adds `bake update`
- [ ] Update upgrades tool-manager tools and, on macOS, Brewfile apps, and does nothing at Apply or Setup time
- [x] A Brewfile syntax check is part of `bake lint`
- [x] "Update" is added to the steering file's times (now four), and ADR 0002 is committed
