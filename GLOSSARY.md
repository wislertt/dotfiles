# dotfiles

A machine's shared shell, tool and script configuration, kept as a public repo with a private companion. This context names the four times work happens and the places things live.

## Language

### Times

**Apply**:
Run with `bake apply`. The ritual that links the repo's files into place and then Asserts that Use will succeed. Cheap and safe to repeat.
_Avoid_: Install, deploy, sync

**Setup**:
Run with `bake setup-dev`. The ritual that prepares a machine: installs what is missing (tools, macOS apps), applies macOS settings that changed, sets up secrets access, and ends with an Apply. Never upgrades anything already installed. Needed once per machine, which on a fresh machine includes getting the tool manager in place, and again when a new tool needs to take effect.
_Avoid_: Install, provision, init, bootstrap

**Update**:
Run with `bake update`, on demand. The ritual that upgrades what is already installed (tools, macOS apps) and applies macOS settings that changed. Setup installs, Update upgrades, and Apply does neither. Apply and Setup never remove; Update removes only old versions and caches it replaced.
_Avoid_: Upgrade, refresh (Refresh is for secrets)

**Tidy**:
Run with `bake tidy`, on demand and not one of the four times. Removes every Stray it can with the manager that owns it, without asking, and lists the rest with the command to run: anything needing an administrator, apps, unknown files in the local bin folder, copies of a mise tool, GitHub signing keys that never expire and GitHub SSH keys. `bake tidy --check` lists them all and fails if there are any, removing nothing. `bake tidy --caches` also clears Disposable caches: unused Docker images and build cache (unused volumes only with `--volumes`) and, on macOS, Mole's user-level caches; `--check` ignores it.
_Avoid_: Clean (`bake clean` is for files in the repo), prune, dedupe

**Stray**:
Something installed on the machine that no declaration accounts for: not in a mise config, not in a Brewfile, and not on a keep list. A copy of a declared mise tool elsewhere on `PATH` (a Homebrew `jq` after `jq` moved to `mise.toml`) is one kind of Stray; system directories, mise shims and project virtualenvs are not. So is a GitHub signing key that has expired or never expires, other than this machine's own, any SSH key on the GitHub account (git uses HTTPS), and a numbered or dated Rust toolchain that no repo under the repos roots in `src/lib/tidy.toml` pins (the `stable`, `beta` and `nightly` channels never are).
_Avoid_: Orphan, leftover, junk

**Keep list**:
The record of things deliberately left installed without a declaration, each with a one-line reason, so Tidy passes over them (`src/lib/keep.toml`, keyed `kind:name` as Tidy prints it). A private keep list in the private companion repo holds those that reveal an account, employer or work setup.
_Avoid_: Allowlist, ignore list, exceptions

**Use**:
Whenever something that invokes our dotfiles runs, such as a linked script or a shell start. Not a command: it happens on its own, and a failure here is a surprise.
_Avoid_: Run time, launch

### Places

**Dotfile group**:
A named set of files that Apply links to one target. A new file in an existing group needs nothing more; a new target needs a new group.
_Avoid_: Module, bundle

**Partly owned file**:
A file an app also rewrites (Claude Code's settings, Zed's settings), where Apply owns only the listed keys and leaves the app's other keys alone. An enforced key is set back on every Apply; a default key is set only while the file lacks it, so the app may change it after that.
_Avoid_: Managed file (a whole-file link), template

**Private group**:
A dotfile group that lives in the private companion repo because it reveals an account, employer or work setup, or is personal.
_Avoid_: Secret group, hidden config

**Assert**:
A check that reports what is missing and changes nothing, the read-only counterpart of Setup's steps. An Apply ends with an Assert that Use will succeed: the age key is present, the secret store token is stored, and each declared secret resolves. Prints no values.
_Avoid_: Preflight, doctor, health check

**Brewfile**:
The macOS-only list of GUI apps that Setup installs and Update upgrades. Casks only, plus mise itself (the bootstrap, so Update upgrades it): anything else the tool manager installs. A private Brewfile in the private companion repo holds apps that reveal an account or employer, and a Role Brewfile holds apps only some machines get.
_Avoid_: Package list, app manifest

**Role**:
A label a machine has in the private machine list (`machines.toml`, keyed by serial number on macOS and the systemd machine ID on Linux, each entry giving the machine's Machine name and roles), such as `work`. A role adds its own Brewfile and Keep list on the machines that have it; a machine not in the list has no roles.
_Avoid_: profile, host

**Machine name**:
A short name the owner gives a machine (lowercase letters, digits and `-`, such as `work-mac`), kept in the private machine list. Setup asks for it on a machine the list does not have and adds it there; anything else that needs it fails and says to run Setup. It is public as part of the Signing key's title on GitHub. CI, which has no private list, sets it with `DOTFILES_MACHINE_NAME`.
_Avoid_: hostname

**Disposable**:
State a machine regenerates and nothing versions, so it is never backed up or edited by hand.
_Avoid_: Temp, cache (a cache is one kind of disposable)

**Signing key**:
The machine's own GPG key for signing commits, created by Setup and never copied off the machine. It expires 30 days out; Setup and Update renew the same key when under half that remains and keep GitHub holding exactly one copy per machine, titled `dotfiles: <machine name> (<machine tag>)`. A machine no longer in use stops renewing, so its key expires and Update offers to delete it from GitHub.
_Avoid_: GPG key (ambiguous with keys added by hand), rotation (renewal keeps the same key)

### Verification

**Fresh-machine job** (workflow `test-e2e-fresh-machine`):
The CI run that follows the fresh-machine path (install the tool manager, Setup, Apply) on a clean runner, with the same commands as a real machine and throwaway secret values. It proves the public repo works without the private companion.
_Avoid_: Bootstrap job, install test

### Secrets

**Secret reference**:
The name of a secret, tracked in the repo, that says what is needed and where to fetch it. Never carries the value.
_Avoid_: Secret, key, token

**Secret value**:
The actual confidential string. It lives only in the secret store and is handed to a program at start; it is never written into a file we manage.
_Avoid_: Secret, key, token, credential

**Refresh**:
Re-fetching secret values into the local cache so the next start sees the current ones. It changes the cache and nothing else.
_Avoid_: Sync, rotate (rotating changes the value itself)
