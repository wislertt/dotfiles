# 06: New-machine parity

Status: ready-for-agent

Blocked by: 02 (Tidy)

Spec: `.tracker/enhancements/spec.md` (stories 38-42).

**What to build:** A new machine gets the same apps and macOS settings as this one. Every hand-installed GUI app is in the public Brewfile, the private Brewfile or a Keep list, and the macOS settings are small per-area scripts.

- [ ] Each app is sorted into a public cask, a private cask, or a Keep list (MDM-managed or not in Homebrew), work-revealing ones private
- [ ] Each cask's adoption of the existing install is checked by hand, so no app is replaced or loses its data
- [ ] `bake tidy --check` lists no apps
- [ ] macOS settings are one small idempotent script per area, rerun only when its content changes, macOS-only and guarded
- [ ] `bake lint` passes
