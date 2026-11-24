# 08: Tool decisions

Status: resolved

Blocked by: 06, 07 (Duplicates report)

Spec: `.tracker/initialization/spec.md`.

**What to build:** Every tool the owner uses has a home. Sort what is installed into mise, the public Brewfile or the private Brewfile, and for each of starship, zed, git, gh, yt-dlp and marimo decide public, private or disposable for its config (or record an explicit skip). Then install the declared copies with Setup and remove the old Homebrew and global copies with `bake duplicates`.

- [x] starship: decision recorded, config added or skipped
- [x] zed: decision recorded, config added or skipped
- [x] git: the shared part is public and the work-specific part is private (included conditionally); decision recorded
- [x] gh: its hosts file is disposable and not versioned; the rest decided
- [x] yt-dlp: decision recorded, config added or skipped
- [x] marimo: decision recorded, config added or skipped
- [x] Every installed tool is declared in mise, the public Brewfile or the private Brewfile, or recorded as deliberately undeclared
- [x] `bake setup-dev` installs the declared copies, then each old copy that `bake duplicates` lists is removed by hand with its own package manager, and a second run lists none
- [x] The Homebrew upgrade TODO in the bakefile is dropped if nothing is left installed by hand in Homebrew

## Comments

Resolved 2026-11-24.

- starship: public, `src/config/starship.toml`.
- zed: public, `src/config/zed/settings.json`.
- git: shared `src/config/git/{config,ignore}` public; `config` includes the private `private.inc`, which includes `personal.inc` and, by `includeIf`, `work.inc`.
- gh: `src/config/gh/config.yml` public; `hosts.yml` disposable, left in `~/.config/gh`, not versioned.
- yt-dlp: public, `src/config/yt-dlp/config`.
- marimo: deleted from the machine; no config.
- Homebrew: `brew leaves` lists only `mise`; `bake duplicates` reports no duplicates; the Homebrew upgrade TODO is gone from the bakefile.
