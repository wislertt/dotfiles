# dotfiles

A machine's shared shell, tool and script configuration, kept as a public repo with a private companion. This context names the four times work happens and the places things live.

## Language

### Times

**Apply**:
Run with `bake apply`. The ritual that links the repo's files into place and then Asserts that Use will succeed. Cheap and safe to repeat.
_Avoid_: Install, deploy, sync

**Setup**:
Run with `bake setup-dev`. The ritual that prepares a machine: installs what is missing (tools, macOS apps), sets up secrets access, and ends with an Apply. Never upgrades anything already installed. Needed once per machine, which on a fresh machine includes getting the tool manager in place, and again when a new tool needs to take effect.
_Avoid_: Install, provision, init, bootstrap

**Update**:
Run with `bake update`, on demand. The ritual that upgrades what is already installed (tools, macOS apps). Setup installs, Update upgrades, and Apply does neither.
_Avoid_: Upgrade, refresh (Refresh is for secrets)

**Use**:
Whenever something that invokes our dotfiles runs, such as a linked script or a shell start. Not a command: it happens on its own, and a failure here is a surprise.
_Avoid_: Run time, launch

### Places

**Dotfile group**:
A named set of files that Apply links to one target. A new file in an existing group needs nothing more; a new target needs a new group.
_Avoid_: Module, bundle

**Private group**:
A dotfile group that lives in the private companion repo because it reveals an account, employer or work setup, or is personal.
_Avoid_: Secret group, hidden config

**Assert**:
A check that reports what is missing and changes nothing, the read-only counterpart of Setup's steps. An Apply ends with an Assert that Use will succeed: the age key is present, the secret store token is stored, and each declared secret resolves. Prints no values.
_Avoid_: Preflight, doctor, health check

**Brewfile**:
The macOS-only list of GUI apps that Setup installs and Update upgrades. Casks only: anything else the tool manager installs. A private Brewfile in the private companion repo holds apps that reveal an account or employer.
_Avoid_: Package list, app manifest

**Disposable**:
State a machine regenerates and nothing versions, so it is never backed up or edited by hand.
_Avoid_: Temp, cache (a cache is one kind of disposable)

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
