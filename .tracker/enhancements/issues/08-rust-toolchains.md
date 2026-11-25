# 08: Rust toolchains in Tidy

Status: resolved

Blocked by: None (Tidy, ticket 02, is done)

Spec: `.tracker/enhancements/spec.md` (story 57, and the "Rust toolchains are a Stray kind" decision).

**What to build:** `bake tidy` treats a Rust toolchain as a Stray when it is not a channel (`stable`, `beta`, `nightly`) and no repo pins it, and removes it with `rustup toolchain uninstall`. `--check` lists them. A Keep list entry keeps one.

- [x] New Stray kind for rustup toolchains, read from `rustup toolchain list`; channels are never Strays
- [x] A toolchain a repo pins is kept: the scan reads `rust-toolchain.toml` (`[toolchain] channel`) and the legacy `rust-toolchain` file at repo roots only, under the repos root; a pin like `1.100` keeps `1.100.0` and any `1.100.x`
- [x] Removal is `rustup toolchain uninstall <name>`, reported like the other kinds; a failure is reported and the rest still run
- [x] Keep list key `rust-toolchain:<name>` is honoured
- [x] Skipped quietly when rustup is not installed
- [x] Tested at the command with `FakeCtx`: canned `rustup toolchain list`, a temp repos root with pinned and unpinned repos, Keep lists; no test touches the real machine
- [x] GLOSSARY (Stray), README, AGENTS.md (`bake tidy` line) and ADR 0003 list the new kind
- [x] `bake lint` and `bake test` pass

## Comments

2026-11-24, context: `stable` upgrades in place, so old numbered toolchains come from repos that pin a version (rustup installs them on first build). Each is about 1.3 GB. rustup has no prune command, and `mise prune` does not touch rustup toolchains. On this machine today: `stable`, `nightly`, `1.100.0`; pins found in `zerv` (`1.100`), `arrow-rs` (`1.100.0`), `example-zerv-flow` (`1.99`), `delta-rs` (`1.95.0`). Kept out of Update because Update removes only what it replaced, and it did not install these.

2026-11-24, scan timing over `~/vault/repos` (64 repos, 4 pins found by every method): `find -maxdepth 3`, 0.02 s; `find` pruning `.git`, `target`, `node_modules`, `.venv`, 1.5 to 1.9 s; `rg --files` (gitignore-aware), 1.9 s. Walking the tree dominates, so the depth limit is what makes it cheap; `rg --max-depth` would do as well.

Open for the owner: where the repos root is set. A default of `~/vault/repos` in public config reveals nothing about who the owner is; a setting beside the Keep lists keeps the layout out of code. Also confirm rustup's auto-install is on (`rustup set auto-install`), since removal relies on a pinned toolchain coming back on use.

2026-11-25, implementation:

- The repos roots are a `repos` list in the public `src/lib/tidy.toml` (owner's choice), starting with `~/vault/repos`. Pins are read one or two folders under each root, so `<root>/<owner>/<repo>` and `<root>/<repo>` both work.
- A dated toolchain (`nightly-2026-01-01`) is a Stray too, kept only by its exact pin; a custom-named toolchain is never one. A `1.100` pin keeps every `1.100.x`.
- The Keep key is the name as rustup prints it, host triple included (`rust-toolchain:1.99.1-aarch64-apple-darwin`).
- A pin file that is unreadable or not a pin counts for nothing; it does not stop Tidy.
- On this machine `bake tidy --check` keeps `1.100.0` (pinned by `zerv` and `arrow-rs`) and finds no Rust Strays.
- Open for the owner: with no `tidy.toml`, or a root that does not exist, no pins are found and every numbered toolchain is removed without a warning; and whether the Keep key should drop the host triple. rustup's auto-install was not changed (no `auto_install` setting in `~/.rustup/settings.toml`, so rustup's default applies).
