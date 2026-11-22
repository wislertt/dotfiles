# dotfiles

A Mac's shared shell, tool and script configuration, kept as a public repo with a private companion. This context names the three times work happens and the places things live.

## Language

### Times

**Apply**:
Run with `bake apply`. The ritual that links the repo's files into place and then checks that Use will succeed. Cheap and safe to repeat.
_Avoid_: Install, deploy, sync

**Setup**:
Run with `bake setup-dev`. The ritual that prepares a machine: tools, secrets access and tooling, ending with an Apply. Needed once per machine, which on a fresh Mac includes getting the tool manager in place, and again when a new tool needs to take effect.
_Avoid_: Install, provision, init, bootstrap

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

**Disposable**:
State a machine regenerates and nothing versions, so it is never backed up or edited by hand.
_Avoid_: Temp, cache (a cache is one kind of disposable)

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
