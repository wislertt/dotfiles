Status: ready-for-agent

# Enhancements: after v1

## Problem Statement

v1 proves a fresh machine reaches a working state, but a machine in daily use drifts. Tools get installed by hand outside any declaration, old tool managers linger with gigabytes of toolchains, dead `PATH` entries survive every new shell, and caches and old tool versions are never pruned. Finding all this took a day of hand inspection at the end of v1, and nothing stops it coming back. The only help today is the Duplicates report, which sees copies of declared tools but nothing that was never declared, and removes nothing.

v1 also left known gaps. Files that apps also rewrite (Claude Code's settings, Zed's settings) are not owned at all. agent-home still links its files into the home folder one at a time by hand. macOS settings are not captured, so a new machine starts with defaults. Workflows are not checked for security issues. A new `latest` release is held back only by mise's 24-hour default, which nothing records. Nothing notices when shell startup gets slow. About forty GUI apps were installed by hand and are in no Brewfile.

Work in the private companion is not safe from the rituals. Setup and Update sync submodules, which checks `private/` out at the commit the public repo pins, detached. Uncommitted changes, a feature branch or unpushed commits there are stranded or carried onto a detached head. Git's status and diff also show a bumped submodule as a bare commit hash, so a reviewer cannot see what the bump brings in.

The bake code itself does not scale. One class holds every concern: secrets, Homebrew, the Setup and Update overrides, required tools, three lint checks, Apply and its assert, and two commands. The repo root is looked up three times. Each enhancement here adds a command or a step, so without a layout the class keeps growing and a reader cannot find where a command lives.

## Solution

A small Tidy ritual finds Strays (anything installed that no declaration and no Keep list accounts for) and removes each one it can with the manager that owns it, without asking. `bake tidy --check` only lists them and fails if there are any. Tidy absorbs Duplicates. Update, after upgrading, drops the old versions and caches it replaced.

First, the bake code is restructured with no behaviour change: one mixin per bake command or bakelib hook family, pure logic in a separate layer, and the bakebook only composing them. Each later enhancement then adds its own command module instead of growing one class.

The other gaps are independent improvements, each shipped on its own:

- a `PATH` that no longer keeps dead entries alive;
- a cooldown on new releases;
- a workflow security linter;
- partial ownership of files apps rewrite;
- agent-home's links moved into Apply;
- every hand-installed app sorted into a Brewfile or a Keep list;
- macOS settings as small per-area scripts;
- a shell-startup time limit in CI;
- a submodule sync that skips `private/` when work is in progress there, and git config that summarises submodule changes in status and diff.

## User Stories

1. As the owner, I want `bake tidy --check` to list every Stray on my machine, so that drift is visible without hand inspection.
2. As the owner, I want `bake tidy --check` to exit nonzero when it finds Strays and zero when it finds none, so that I can use it as a check.
3. As the owner, I want `bake tidy --check` to remove nothing, so that I can run it any time without risk.
4. As the owner, I want `bake tidy` to remove every Stray it can without asking, so that tidying needs no decisions once the Keep lists are right.
5. As the owner, I want each Stray removed with the manager that owns it, so that the manager's own records stay correct.
6. As the owner, I want Homebrew formulas nothing depends on, and casks, counted as Strays when no Brewfile declares them, so that dependencies of declared apps are never offered for removal.
7. As the owner, I want Homebrew's orphaned dependencies removed after Tidy uninstalls a formula, so that removing one thing leaves nothing behind.
8. As the owner, I want `uv tool` tools, `cargo install` tools and global npm and pnpm packages reported, so that tools installed outside mise are found.
9. As the owner, I want dead links in `PATH` directories reported and removable, so that broken commands disappear.
10. (Dropped 2026-11-24.) Missing `PATH` directories are not reported: the answer depends on which terminal runs bake (Orca adds fixed tool folders whether or not they exist), a missing folder does no harm, and the fix is editing config, which bake does not do.
11. As the owner, I want leftover tool-manager folders (asdf, pyenv, nvm, bun, conda, a hand-installed Go) reported, so that tens of gigabytes of old toolchains are found.
12. As the owner, I want a leftover folder in my home made writable before it is removed, so that read-only caches do not make removal fail halfway.
13. As the owner, I want anything that needs an administrator only named, with the command to run, so that bake never runs sudo.
14. As the owner, I want GUI apps not in a Brewfile only named, never removed, so that an app I rely on is never deleted by a script.
15. As the owner, I want unknown regular files in my local bin folder named but never offered for removal, so that a file that may hold credentials is never read or deleted by bake.
16. As the owner, I want copies of a declared mise tool elsewhere on `PATH` reported by Tidy, so that Duplicates and Tidy are one command and cannot drift apart.
17. As the owner, I want a public Keep list, so that something deliberately left undeclared stops being reported.
18. As the owner, I want each Keep-list entry to carry a one-line reason, so that I remember later why it was kept.
19. As the owner, I want a private Keep list in the private companion, so that entries revealing an employer or work setup stay out of the public repo.
20. As a stranger cloning only the public repo, I want Tidy to work without the private companion, so that the public repo stays usable alone.
21. As the owner, I want `bake tidy --check` kept out of CI, so that the software preinstalled on a runner does not fail the build.
22. As the owner, I want `bake update` to prune old mise tool versions after upgrading, so that disk use does not grow without bound.
23. As the owner, I want `bake update` to prune uv's cache, so that old Python packages do not pile up.
24. As the owner, I want `bake update` to run Homebrew's cleanup on macOS, so that old app versions and downloads go away.
25. As the owner, I want Setup and Apply still never to remove anything, so that the rituals I run often stay safe.
26. As the owner, I want dead `PATH` entries gone after one fresh login, so that removed tool managers stop appearing in GUI apps and new shells.
27. As the owner, I want GUI apps such as Zed and Orca still to find mise tools after that fix, so that the fix breaks nothing.
28. As the owner, I want a new `latest` release held back for a day before mise installs it, so that a compromised release has time to be caught.
29. As the owner, I want to exempt a single tool from that cooldown when I need a fix urgently, so that the cooldown never blocks me.
30. As the owner, I want every workflow checked for security issues in `bake lint --slow` and CI, so that a risky workflow pattern never lands.
31. As the owner, I want each workflow finding either fixed or allowed with a reason, so that the linter stays quiet without hiding real issues.
32. As the owner, I want the private repo's workflows checked the same way, so that both repos meet the same bar.
33. As the owner, I want to own only the keys I care about in a file an app also rewrites, so that the app's own changes and mine both survive.
34. As the owner, I want a rerun of Apply on a partly owned file to change nothing, so that Apply stays idempotent.
35. As the owner, I want each partly owned file to have a public or private decision, so that it lands in the right home.
36. As the owner, I want agent-home's files linked by Apply instead of by hand, so that a new machine gets them without manual steps.
37. As the owner, I want Apply still to work on a machine without agent-home, so that the public repo stays usable alone.
38. As the owner, I want every hand-installed GUI app put in the public Brewfile, the private Brewfile or a Keep list, so that a new machine gets the same apps and nothing is unaccounted for.
39. As the owner, I want each app's move into Homebrew checked so that Homebrew adopts the existing install without replacing or breaking it, so that no app loses its data or settings.
40. As the owner, I want apps managed by my employer's device management kept on the private Keep list, so that bake never fights the MDM.
41. As the owner, I want my macOS settings captured as small scripts, one per area (Dock, Finder, keyboard and so on), so that each area can change on its own.
42. As the owner, I want each settings script to rerun only when it changes, so that applying settings is fast and repeatable.
43. As the owner, I want CI to fail when interactive shell startup exceeds a time limit, so that a slow shell module is caught before it lands.
44. As a future reader, I want an ADR explaining why Tidy removes things after v1 chose report-only, so that the reversal is not a surprise.
45. As a contributor, I want each bake command's code in its own module, so that I can find and change one command without reading the rest.
46. As a contributor, I want the bakebook to only compose the command mixins, so that the full list of features is visible in one place.
47. As a contributor, I want pure logic (Brewfile line checks, shell-file classification, signing plans, duplicate finding) kept apart from bakelib, so that it can be read and tested without a fake context.
48. As a contributor, I want logic shared by several commands (the Brewfiles, the signing key) in one shared module, so that Setup, Update, lint and the signing command cannot drift apart.
49. As a contributor, I want the repo root defined once, so that moving a file cannot quietly break a path.
50. As a contributor adding a feature, I want a written rule for where its code goes, so that the layout holds as features grow.
51. As the owner, I want the restructure to change no behaviour, so that every command acts exactly as before and the restructure is safe to land alone.
52. As a contributor, I want tests laid out like the code, so that each module's tests are next to each other and easy to find.
53. As an agent working on a later enhancement, I want the restructure landed first, so that Tidy and Update's prune go straight into their own modules.
54. As the owner, I want Setup and Update to skip the submodule sync, with a warning saying why, when `private/` has uncommitted changes, a branch other than main checked out, or commits not on origin/main, so that work in progress there is never stranded on a detached head.
55. As the owner, I want the sync to run as before when `private/` is clean on main, or is not checked out at all, so that the guard changes nothing in the normal case and the public repo still works alone.
56. As the owner, I want `git status` and `git diff` to list the commits a submodule bump brings in, so that I can review a bump without opening the submodule.
57. As the owner, I want Tidy to remove Rust toolchains that no repo of mine pins (keeping the `stable`, `beta` and `nightly` channels), so that old pinned toolchains of over 1 GB each stop piling up.

## Implementation Decisions

- **Bake code layout.** The bakebook only composes mixins and exposes the bakebook object. Commands live in a commands layer, one mixin per bake command or bakelib hook family: Apply (with its assert), the Setup and Update overrides (tools, Brewfile steps, required tools), lint (shell, Brewfiles, global fnox), secrets (fetch functions and the secret key names), duplicates, and the signing clean-up command. Pure logic with no bakelib import lives in a core layer: Brewfiles (paths, line check), signing (today's module, moved), duplicates (today's module, moved) and shell-file classification. The repo root is one constant. It is called core, not lib, because the repo's lib folder already means repo files that are not linked. bakelib already defines commands on mixins (its submodules mixin), so this needs nothing new from bakelib.
- **The restructure changes no behaviour** and lands before Tidy and Machine hygiene. A fix found during it is listed for the owner, not made.
- **Commands end in their own module.** Duplicates moves to its command module now, and Tidy replaces it with a Tidy module. The signing clean-up command moves to a signing command module, and if GitHub key clean-up is rehomed later, only that module moves.
- **The layout rule is written down**, not in an ADR (it is easy to reverse): the steering file's layout section and the contributing guide say a new command is a new command mixin, its pure logic goes in core, and it is added to the bakebook.
- **Tidy replaces Duplicates.** A Duplicate is one kind of Stray, and two commands over overlapping ground would drift. Duplicates' rules carry over unchanged: system directories, mise shims and project virtualenvs are not reported, and a tool mise has not installed is not reported.
- **Tidy reverses v1's report-only choice** (v1 ticket 07). That choice was safe while removal meant per-manager code run without asking. `--check` as a preview, with Keep lists, makes removal safe enough. A new ADR (0003) records the reversal.
- **Stray kinds:**
    - Homebrew formulas that nothing depends on, and casks, minus both Brewfiles. Homebrew's own bundle cleanup listing, run without its force flag, gives exactly this set;
    - `uv tool`, `cargo install`, and global npm and pnpm packages;
    - dead links in `PATH` directories;
    - known leftover tool-manager folders;
    - on macOS, apps not in a Brewfile;
    - copies of declared mise tools;
    - unknown regular files in the local bin folder.
- **Rust toolchains are a Stray kind** (changed 2026-11-24, story 57). A numbered toolchain is a Stray unless a repo pins it. The scan reads `rust-toolchain.toml` and `rust-toolchain` at repo roots only (depth-limited, about 20 ms over 64 repos, against about 2 s for a full walk with `find` or `rg`). A pin nested deeper is missed; its toolchain is removed and rustup installs it again on the next build there.
- **Removal actions:**
    - uninstall with the owning manager, then Homebrew's autoremove after any Homebrew uninstall;
    - `rm` for a dead link;
    - make writable, then remove, for a leftover folder in the home directory;
    - only print the command, for anything needing sudo, apps, and unknown local bin files.
- **Keep lists** are TOML files, one public and one in the private companion. Each entry is a `kind:name` key with a one-line reason. They start from the items v1 ticket 08 recorded as deliberately undeclared.
- **`--check`** exits nonzero on any Stray and does not run in CI.
- **Update's prune** runs mise's prune, uv's cache prune and, on macOS, Homebrew's cleanup, after the upgrades. The steering rule becomes "Apply and Setup never remove; Update removes only old versions and caches it replaced". The glossary's Update entry widens to match.
- **launchctl:** the zsh tools module saves each shell's inherited `PATH` for GUI apps, so a dead entry is passed back into every later shell. Build the saved `PATH` fresh, or drop the step if GUI apps no longer need it. macOS-only, guarded.
- **Release cooldown:** mise's default `minimum_release_age` of 24 hours, with no setting of our own: it covers every backend that reports release dates and, for `npm:` and `pypi:`, transitive dependencies. A week was considered and dropped: most compromised releases are caught within a day, and a week delays fixes too. ADR 0002 notes the cooldown next to "latest, no lockfile".
- **Workflow linter:** zizmor, a mise tool run by `bake lint --slow`, so the pre-commit workflow runs it (with the job's token, for the online audits). Not a pre-commit hook: with a GitHub token its online audits take seconds on every workflow commit.
- **Partly owned files:** mise's dotfile merge mode, which owns only the listed keys. Avoid any mode that writes a secret into a file.
- **agent-home links:** first decide whether a private dotfile group points at the agent-home checkout, or the files move into dotfiles. agent-home is a separate private repo.
- **macOS settings:** one small idempotent script per area, rerun only when its content changes. macOS-only.
- **Shell-startup budget:** a CI step times interactive zsh startup against a loose limit.
- **Private work-in-progress guard:** before the submodule sync, the bakebook checks `private/` with three git reads (porcelain status, current branch, commits ahead of origin/main). Any one of them means work in progress: the sync is skipped with a warning naming the reason, and the run continues. No `private/` checkout means no guard. The check reads only; it never stashes, commits or switches branches. It lands now, in the current bakebook, and moves with the Setup and Update overrides in the restructure.
- **Submodule visibility:** the linked git config sets `status.submoduleSummary` and `diff.submodule = log`. Same on every machine and reveals nothing, so it is public.

## Testing Decisions

- **The restructure** is proven by the existing tests. Command tests (with `FakeCtx`) are the seam: they move to mirror the commands layer and only their imports and locations change. The existing pure-function tests for signing and duplicates move to mirror the core layer. No new seam and no new core-only tests; `FakeCtx` stays shared.
- A good test observes only external behavior: what is listed, the exit code, which commands would run, and the files and links that result. It never asserts on internal calls or on log wording.
- **Tidy and Update** are tested at the bake command, with `FakeCtx`. Canned manager outputs, a temp home directory, `PATH` and Keep lists stand in for the machine, and no test touches the real one. The current unit tests for the duplicates helper function become command tests, so Tidy has a single seam. Prior art: the Setup and Update tests and the duplicates tests.
- **Partly owned files and the agent-home links** are tested by the existing integration test: real mise in a throwaway home directory. It checks that owned keys merge in, the app's other keys survive, a rerun changes nothing, and Apply works without agent-home.
- **Not tested automatically:**
    - the launchctl fix, the macOS settings and the Brewfile moves, which need real macOS state and are verified once by hand;
    - the release cooldown and the workflow linter, which are configuration exercised by `bake lint` and CI.

    The shell-startup budget is itself a CI check.

- **The private work-in-progress guard** is tested at the submodule sync with `FakeCtx`: a canned git output for each reason (uncommitted, feature branch, unpushed) skips the sync, and a clean main or a missing checkout syncs. The git config is configuration and is not tested.

## Out of Scope

- **Rollback and a machine-local override layer:** not needed, because mise already has dotfile rollback and undo, and a local config file.
- **Later, not now:**
    - SSH commit signing, since GPG signing was just set up;
    - an xdg-ninja report of home-folder clutter;
    - a Codespaces or dev-container entry point;
    - mise's absent mode for retired links, which is removal during Apply;
    - editor config beyond Zed;
    - a real Linux machine.
- Restructuring the private companion's bakefile. It is a separate repo and can follow the same layout later.

## Further Notes

- **Tickets:** 01 Structure the bake code (stories 45-53), 02 Tidy (blocked by 01), 03 Machine hygiene (blocked by 01), 04 CI and supply-chain guards, 05 Own more config, 06 New-machine parity (blocked by 02), 07 Protect private work in progress (stories 54-56, landed ahead of 01). The rest can start in any order.
- **Origin:** the machine cleanup at the end of v1 ticket 08, and a survey of public dotfiles in the agent-home wiki (dotfiles research notes).
- **Glossary:** Tidy, Stray and Keep list are already defined. Duplicates leaves the glossary when Tidy lands.
