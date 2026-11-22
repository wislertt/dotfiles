# 07: Tool decisions and v1 gate

Status: ready-for-human

Blocked by: 01, 02, 03, 04, 05, 06

Spec: `.tracker/initialization/spec.md`.

**What to build:** Every tool the owner uses has a home, and the v1 gate is checked. For each of starship, zed, git, gh, yt-dlp and marimo, decide public, private or disposable and put the config where it belongs (or record an explicit skip). Then run the final checks and one real new-machine run.

- [ ] starship: decision recorded, config added or skipped
- [ ] zed: decision recorded, config added or skipped
- [ ] git: the shared part is public and the work-specific part is private (included conditionally); decision recorded
- [ ] gh: its hosts file is disposable and not versioned; the rest decided
- [ ] yt-dlp: decision recorded, config added or skipped
- [ ] marimo: decision recorded, config added or skipped
- [ ] `mise dotfiles diff` reviewed with no surprises
- [ ] A clean secret scan over the full history of the public and private repos
- [ ] One real new-machine run of `mise install`, `bake setup-dev` and `bake apply` works
- [ ] Each v1 gate item in the spec is ticked off, and the owner confirms v1
