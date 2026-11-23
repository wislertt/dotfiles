Status: ready-for-agent

# Enhancements: after v1

## Problem Statement

v1 proves a fresh machine reaches a working state, but a machine in daily use drifts. Tools get installed by hand outside any declaration, old tool managers linger with gigabytes of toolchains, dead `PATH` entries survive every new shell, and caches and old tool versions are never pruned. Finding all this took a day of hand inspection at the end of v1, and nothing stops it coming back. The only help today is the Duplicates report, which sees copies of declared tools but nothing that was never declared, and removes nothing.

v1 also left known gaps. Files that apps also rewrite (Claude Code's settings, Zed's settings) are not owned at all. agent-home still links its files into the home folder one at a time by hand. macOS settings are not captured, so a new machine starts with defaults. Workflows are not checked for security issues. A new `latest` release installs the day it appears, before a compromised one could be noticed. Nothing notices when shell startup gets slow. About forty GUI apps were installed by hand and are in no Brewfile.

## Solution

A small Tidy ritual finds Strays (anything installed that no declaration and no Keep list accounts for) and removes them one at a time with the manager that owns them, asking first. `bake tidy --check` only lists them and fails if there are any. Tidy absorbs Duplicates. Update, after upgrading, drops the old versions and caches it replaced.

The other gaps are independent improvements, each shipped on its own:

- a `PATH` that no longer keeps dead entries alive;
- a cooldown on new releases;
- a workflow security linter;
- partial ownership of files apps rewrite;
- agent-home's links moved into Apply;
- every hand-installed app sorted into a Brewfile or a Keep list;
- macOS settings as small per-area scripts;
- a shell-startup time limit in CI.

## User Stories

1. As the owner, I want `bake tidy --check` to list every Stray on my machine, so that drift is visible without hand inspection.
2. As the owner, I want `bake tidy --check` to exit nonzero when it finds Strays and zero when it finds none, so that I can use it as a check.
3. As the owner, I want `bake tidy --check` to remove nothing, so that I can run it any time without risk.
4. As the owner, I want `bake tidy` to ask y/N for each Stray, so that something still needed survives a quick read.
5. As the owner, I want each Stray removed with the manager that owns it, so that the manager's own records stay correct.
6. As the owner, I want Homebrew formulas nothing depends on, and casks, counted as Strays when no Brewfile declares them, so that dependencies of declared apps are never offered for removal.
7. As the owner, I want Homebrew's orphaned dependencies removed after Tidy uninstalls a formula, so that removing one thing leaves nothing behind.
8. As the owner, I want `uv tool` tools, `cargo install` tools and global npm and pnpm packages reported, so that tools installed outside mise are found.
9. As the owner, I want dead links in `PATH` directories reported and removable, so that broken commands disappear.
10. As the owner, I want `PATH` entries that point to missing directories reported, so that I can see stale `PATH` setup.
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
28. As the owner, I want a new `latest` release held back for a week before mise installs it, so that a compromised release has time to be caught.
29. As the owner, I want to exempt a single tool from that cooldown when I need a fix urgently, so that the cooldown never blocks me.
30. As the owner, I want every workflow checked for security issues in `bake lint` and CI, so that a risky workflow pattern never lands.
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

## Implementation Decisions

- **Tidy replaces Duplicates.** A Duplicate is one kind of Stray, and two commands over overlapping ground would drift. Duplicates' rules carry over unchanged: system directories, mise shims and project virtualenvs are not reported, and a tool mise has not installed is not reported.
- **Tidy reverses v1's report-only choice** (v1 ticket 07). That choice was safe while removal meant per-manager code run without asking. Asking per Stray, with Keep lists, makes removal safe enough. A new ADR (0003) records the reversal.
- **Stray kinds:**
    - Homebrew formulas that nothing depends on, and casks, minus both Brewfiles. Homebrew's own bundle cleanup listing, run without its force flag, gives exactly this set;
    - `uv tool`, `cargo install`, and global npm and pnpm packages;
    - dead links in `PATH` directories;
    - missing `PATH` directories;
    - known leftover tool-manager folders;
    - on macOS, apps not in a Brewfile;
    - copies of declared mise tools;
    - unknown regular files in the local bin folder.
- **Rust toolchains are not Stray kinds.** Knowing which ones a repo pins would mean scanning repos.
- **Removal actions:**
    - uninstall with the owning manager, then Homebrew's autoremove after any Homebrew uninstall;
    - `rm` for a dead link;
    - make writable, then remove, for a leftover folder in the home directory;
    - only print the command, for anything needing sudo, apps, and unknown local bin files.
- **Keep lists** are TOML files, one public and one in the private companion. Each entry is a `kind:name` key with a one-line reason. They start from the items v1 ticket 08 recorded as deliberately undeclared.
- **`--check`** exits nonzero on any Stray and does not run in CI.
- **Update's prune** runs mise's prune, uv's cache prune and, on macOS, Homebrew's cleanup, after the upgrades. The steering rule becomes "Apply and Setup never remove; Update removes only old versions and caches it replaced". The glossary's Update entry widens to match.
- **launchctl:** the zsh tools module saves each shell's inherited `PATH` for GUI apps, so a dead entry is passed back into every later shell. Build the saved `PATH` fresh, or drop the step if GUI apps no longer need it. macOS-only, guarded.
- **Release cooldown:** mise's minimum release age setting, 7 days, in both the repo mise config and the global one. The setting name and its per-tool exclusion are to be checked against the mise security docs first. ADR 0002 notes the cooldown next to "latest, no lockfile".
- **Workflow linter:** zizmor, run as a pre-commit hook so `bake lint` and the pre-commit workflow both run it.
- **Partly owned files:** mise's dotfile merge mode, which owns only the listed keys. Avoid any mode that writes a secret into a file.
- **agent-home links:** first decide whether a private dotfile group points at the agent-home checkout, or the files move into dotfiles. agent-home is a separate private repo.
- **macOS settings:** one small idempotent script per area, rerun only when its content changes. macOS-only.
- **Shell-startup budget:** a CI step times interactive zsh startup against a loose limit.

## Testing Decisions

- A good test observes only external behavior: what is listed, the exit code, which commands would run, and the files and links that result. It never asserts on internal calls or on log wording.
- **Tidy and Update** are tested at the bake command, with `FakeCtx`. Canned manager outputs, a temp home directory, `PATH` and Keep lists stand in for the machine, and no test touches the real one. The current unit tests for the duplicates helper function become command tests, so Tidy has a single seam. Prior art: the Setup and Update tests and the duplicates tests.
- **Partly owned files and the agent-home links** are tested by the existing integration test: real mise in a throwaway home directory. It checks that owned keys merge in, the app's other keys survive, a rerun changes nothing, and Apply works without agent-home.
- **Not tested automatically:**
    - the launchctl fix, the macOS settings and the Brewfile moves, which need real macOS state and are verified once by hand;
    - the release cooldown and the workflow linter, which are configuration exercised by `bake lint` and CI.

    The shell-startup budget is itself a CI check.

## Out of Scope

- **Rollback and a machine-local override layer:** not needed, because mise already has dotfile rollback and undo, and a local config file.
- **Later, not now:**
    - SSH commit signing, since GPG signing was just set up;
    - an xdg-ninja report of home-folder clutter;
    - a Codespaces or dev-container entry point;
    - mise's absent mode for retired links, which is removal during Apply;
    - editor config beyond Zed;
    - a real Linux machine.
- Pruning unused Rust toolchains.

## Further Notes

- **Tickets:** 01 Tidy, 02 Machine hygiene, 03 CI and supply-chain guards, 04 Own more config, 05 New-machine parity (blocked by 01). The rest can start in any order.
- **Origin:** the machine cleanup at the end of v1 ticket 08, and a survey of public dotfiles in the agent-home wiki (dotfiles research notes).
- **Glossary:** Tidy, Stray and Keep list are already defined. Duplicates leaves the glossary when Tidy lands.
