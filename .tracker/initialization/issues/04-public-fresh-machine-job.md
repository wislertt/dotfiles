# 04: Public Fresh-machine job and CI secrets

Status: ready-for-agent

Blocked by: 01 (Safe, standalone Apply), 02 (Tools, Brewfile and Update), 03 (Public CI and versioning)

Spec: `.tracker/initialization/spec.md`.

**What to build:** CI proves that the public repo reaches a working machine from nothing, using the same commands as a real machine and no real secrets. A Fresh-machine job installs the tool manager, runs Setup (including the Brewfile apps on macOS), runs Apply twice, and asserts the local check's outcomes, on macOS and Linux. It uses a CI-only secrets project with dummy values.

**Owner prerequisite (do first, then mark this ticket ready):** create a dummy Bitwarden project with the same `DOTFILES_*` names and dummy values, and a machine account granted only that project; store its token as a repository secret.

- [x] Verify that an fnox profile can override the provider's `project_id` (fallback: a second provider block) and record the result in the spec
- [x] Verify whether Setup can store the secret-store token and create the age key without a human; if not, add the smallest non-interactive path and record it (none needed: CI runs `bake secret set` after `bake setup-fnox`)
- [x] A `ci` fnox profile points at the dummy project; CI sets the profile and the token, and Apply's Assert passes unchanged
- [x] The Fresh-machine job runs Setup and Apply twice on `macos-latest` and `ubuntu-latest` with `fail-fast: false`, checks out with `submodules: false`, and runs on every pull request (through `ci.yml`, no path filter: the job is short enough that a filter could only hide a regression) and weekly
- [x] The macOS job runs the full Brewfile step; the first run's duration and any flakiness are measured and recorded; a cache is added, then an opt-out, only if it is slow or flaky (first green run on PR #4: macOS job 3m47s, of which `setup-dev` 3m13s; Ubuntu job 31s; no flakiness seen in that run; no cache or opt-out added; re-measure over the weekly runs)
- [x] If Linux fails for a reason that needs real work, its matrix entry is commented out with a TODO naming the cause, and macOS stays green (not needed: Ubuntu is green)
- [x] No real secret value is ever available to CI, and no private file name appears in the logs (the repo secret `BWS_ACCESS_TOKEN_DEV` is the dummy-project token set up in the owner prerequisite, and no other repo secret exists; `setup-dev` tries `git submodule update --init` and fails to clone `private` without credentials, which prints only the submodule URL already in `.gitmodules`)
