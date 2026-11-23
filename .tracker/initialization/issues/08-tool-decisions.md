# 08: Tool decisions

Status: ready-for-human

Blocked by: 06, 07 (Duplicates report)

Spec: `.tracker/initialization/spec.md`.

**What to build:** Every tool the owner uses has a home. Sort what is installed into mise, the public Brewfile or the private Brewfile, and for each of starship, zed, git, gh, yt-dlp and marimo decide public, private or disposable for its config (or record an explicit skip). Then install the declared copies with Setup and remove the old Homebrew and global copies with `bake duplicates`.

- [ ] starship: decision recorded, config added or skipped
- [ ] zed: decision recorded, config added or skipped
- [ ] git: the shared part is public and the work-specific part is private (included conditionally); decision recorded
- [ ] gh: its hosts file is disposable and not versioned; the rest decided
- [ ] yt-dlp: decision recorded, config added or skipped
- [ ] marimo: decision recorded, config added or skipped
- [ ] Every installed tool is declared in mise, the public Brewfile or the private Brewfile, or recorded as deliberately undeclared
- [ ] `bake setup-dev` installs the declared copies, then each old copy that `bake duplicates` lists is removed by hand with its own package manager, and a second run lists none
- [ ] The Homebrew upgrade TODO in the bakefile is dropped if nothing is left installed by hand in Homebrew
