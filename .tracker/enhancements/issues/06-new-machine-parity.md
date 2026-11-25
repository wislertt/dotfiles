# 06: New-machine parity

Status: done

Blocked by: 02 (Tidy)

Spec: `.tracker/enhancements/spec.md` (stories 38-42).

**What to build:** A new machine gets the same apps and macOS settings as this one. Every hand-installed GUI app is in the public Brewfile, the private Brewfile or a Keep list, and the macOS settings are small per-area scripts.

- [x] Each app is sorted into a public cask, a private cask, or a Keep list (MDM-managed or not in Homebrew), work-revealing ones private
- [x] Each cask's adoption of the existing install is checked by hand, so no app is replaced or loses its data
- [x] `bake tidy --check` lists no apps
- [x] macOS settings are one small idempotent script per area, rerun only when its content changes, macOS-only and guarded
- [x] `bake lint` passes

## Progress

- Sorted, all private for now (the owner promotes to public later): 19 casks in `private/src/lib/Brewfile`, 13 apps on `private/src/lib/keep.toml`. Firefox, PyCharm CE and Amazon Q 2 deleted as unused. Only Defender and Company Portal are MDM-managed; Office and OneDrive are App Store installs (receipt `Production`, not `ProductionVPP`).
- Tidy counts an app as a cask's when its uninstall deletes it or one of its `pkgutil` receipts holds it, so pkg casks (zoom, google-drive, microsoft-teams and so on) account for their apps.
- Adopted in place by `brew install --cask --adopt` (inode and version unchanged): chatgpt, dbeaver-community, discord, google-chrome, macsyzones, notion, obsidian, postman, visual-studio-code, vivaldi, webex.
- Bake runs commands without a terminal, so a cask's sudo could not ask for a password. `brew bundle` now gets `SUDO_ASKPASS` (`src/lib/sudo-askpass`, a macOS dialog) and `HOMEBREW_CASK_OPTS=--adopt`, and every Brewfile runs before Setup reports the ones that failed. With that, `bake setup-dev` adopted shottr and cursr (unchanged) and ran the installers of displaylink, google-drive, logi-options+, microsoft-teams, openvpn-connect and zoom over the existing apps: same paths, no second copies. `bake tidy --check` is clean.
- Settings: `private/src/lib/macos/{appearance,desktop,dock,keyboard,trackpad}.sh`, only values that differ from macOS defaults; run once by hand, values read back unchanged.
- Per-machine apps: `private/src/lib/machines.toml` maps this Mac's serial to the `work` role. `Brewfile.work` holds microsoft-teams, openvpn-connect, webex and zoom; `keep.work.toml` holds Company Portal, Microsoft Defender, the Office apps and OneDrive. Setup, Update and Tidy add a role's files only on a machine with that role; lint checks every role Brewfile.
