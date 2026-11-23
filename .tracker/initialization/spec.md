Status: ready-for-agent

# Initialization: dotfiles v1

## Problem Statement

The dotfiles work, but only on the one machine where they were built. Nothing proves that a fresh machine reaches a working state, and several things would break it: Apply overwrites existing files with `--force`, a clone of the public repo without the private companion cannot Apply at all, Setup depends on Homebrew on every platform, and Setup upgrades what it installs. The repo also lacks what makes a public repo trustworthy and maintainable: CI, a license, dependency updates, contribution and tracker docs, and a README a stranger can follow. As the owner, I cannot yet rely on a new machine, a CI run or a reader of the repo to behave the way my own machine does.

## Solution

Make the Fresh-machine path (install the tool manager, Setup, Apply) work the same on any machine and prove it in CI. Apply becomes safe by default and never overwrites unmanaged files. The public repo works alone, and the private companion adds its groups when present. Tools are installed by the tool manager at `latest`, with a hand pin only when a release breaks one. macOS GUI apps come from a Brewfile, applied on macOS only. A new Update ritual upgrades what is installed on demand, and Setup installs what is missing. Both repos get the same CI, versioning and docs, modelled on the bakefile repo, so the process can be reused for any repo.

## User Stories

1. As the owner, I want a Fresh-machine job in CI that runs the real Setup and Apply on a clean runner, so that I know a new machine will work before I own one.
2. As the owner, I want that job to run on macOS and Linux, so that "platform-agnostic" is proven and not only claimed.
3. As the owner, I want a failing Linux job to be commented out with a TODO instead of blocking everything, so that macOS coverage stays while the Linux gap is tracked.
4. As the owner, I want the Fresh-machine job to run on pull requests that touch setup-related files and on a weekly schedule, so that regressions and upstream drift are both caught.
5. As the owner, I want CI to run the same commands I run locally, so that a green CI means something about my machine.
6. As the owner, I want Apply to refuse to overwrite an existing regular file and to name it, so that a first Apply on a machine with existing config cannot destroy anything.
7. As the owner, I want Apply to leave the refused file untouched and exit non-zero, so that I can resolve the conflict by hand.
8. As the owner, I want the failure message to say how to resolve a conflict, including that forcing is a manual choice made outside `bake`, so that the dangerous option is never the default.
9. As the owner, I want a second Apply on an already-applied machine to change nothing, so that Apply is safe to repeat.
10. As the owner, I want it documented that Apply replaces a symlink that points elsewhere, so that this one unprotected case is not a surprise.
11. As a stranger reading the repo, I want the public repo to Apply on its own without the private companion, so that I can use it as a reference.
12. As the owner, I want a new machine that cannot yet reach the private repo to still get a working public setup, so that I am not blocked by auth order.
13. As the owner, I want private groups to load automatically when the private companion is present, so that my own machine behaves as it does today.
14. As the owner, I want Setup to install what is missing and never upgrade the mise tools, so that re-running Setup does not change the versions of the tools in the repo (for now it also upgrades Homebrew, until nothing there is installed by hand).
15. As the owner, I want an Update ritual that upgrades tools and macOS apps on demand, so that upgrades are deliberate.
16. As the owner, I want every command-line tool installed by the tool manager at `latest`, with a hand pin only when a release breaks something, so that there is nothing to maintain until an edge case appears.
17. As the owner, I want `bake update` to upgrade tools on demand, and the weekly Fresh-machine job to catch upstream drift, so that a bad release is found without a bump-PR chore.
18. As the owner, I want macOS GUI apps listed in a public Brewfile and a private Brewfile, so that apps that reveal an account or employer stay private.
19. As the owner, I want Brewfile apps applied only on macOS and never removed by Setup or Update, so that apps I installed by hand are not uninstalled.
20. As the owner, I want a fresh macOS install of the Brewfile apps tested in CI, with a cache or an opt-out added only if it proves slow or flaky, so that I measure before optimizing.
21. As the owner, I want adoption of hand-installed apps verified once by hand, so that my existing Orca, Zed and Docker are not reinstalled.
22. As the owner, I want no Brewfile lock file written, so that updates do not produce noisy diffs for versions that cannot be reproduced anyway.
23. As the owner, I want the Assert at the end of Apply to reuse the shared bake asserts for the age key and secret-store token, plus one check that each declared secret resolves, so that the repo carries no hand-rolled copy of shared logic.
24. As the owner, I want every Assert message to say what is missing, so that I know what failed without reading code.
25. As the owner, I want CI to run Apply's Assert unchanged against a CI-only secrets project with dummy values, so that the Assert is exercised without any real secret reaching CI.
26. As the owner, I want a CI profile that points at the dummy project and a machine account that can see only that project, so that a CI leak cannot expose a real secret.
27. As the owner, I want to know early whether Setup can store the secret-store token and create the age key without a human, so that the CI design does not rest on an assumption.
28. As the owner, I want public CI to check out no submodules, so that private file names never appear in world-readable logs.
29. As the owner, I want the private repo's CI to run the combined Fresh-machine job (public at main plus private), so that private groups and the full path are tested where only I can read the logs.
30. As the owner, I want that combined job to run on a schedule as well, so that public changes that break the private groups are caught.
31. As the owner, I want the private repo to have the full CI set (formatting and lint, security scan, pull request title check, versioning), so that it is held to the same bar as public.
32. As the owner, I want the same versioning and tags on both repos, so that the public tag pins a reproducible state including the private pointer.
33. As the owner, I want pull request titles checked as conventional commits, so that versioning can be automatic.
34. As the owner, I want every workflow action pinned by commit SHA with its version in a comment and minimal permissions, so that CI is not a supply-chain hole.
35. As the owner, I want a daily and on-push security scan with a secret scanner over history, so that a leaked secret is found quickly.
36. As the owner, I want `bake lint` to remain the one local entry point for static checks, including shell lint and Brewfile syntax, so that I run one command before committing.
37. As the owner, I want a license file matching my other repos, so that the public repo is clearly licensed.
38. As a contributor, I want a contributing guide that points to the standards, glossary and decisions, so that I know the workflow.
39. As an agent, I want the tracker, triage-label and domain docs in place, so that skills publish and read work in the way the repo expects.
40. As an agent, I want the repo's steering file to list those docs under an agent-skills section, so that I find them without being told.
41. As a reader of the repo, I want decisions that are hard to reverse and surprising recorded as ADRs, so that nobody undoes them by accident.
42. As the owner, I want the glossary to name Update, Assert, Brewfile and the Fresh-machine job, so that docs, code and conversation use one vocabulary.
43. As the owner, I want every remaining use of the old word "preflight" renamed, so that terms match bake's own.
44. As a stranger, I want a README that explains the four homes, the four times, the Fresh-machine path, what is macOS-only, and what to do on a conflict, so that I can follow it without asking.
45. As the owner, I want the steering file to say that macOS and Linux are tested in CI once Linux passes, and macOS only until then, so that the claim matches the evidence.
46. As the owner, I want each tool I use today to get a decision (public, private or disposable) and its config added where it belongs, so that nothing I rely on is left unmanaged.
47. As the owner, I want a clean secret scan of the full history of both repos before anything is pushed, so that a past mistake is not published.
48. As the owner, I want a diff check that shows what Apply would change before I rely on it, so that I can review changes to my machine.

## Implementation Decisions

- **Seam.** One seam, the Fresh-machine path, run black-box in a clean environment. It runs the real tool-manager install, Setup, Apply and a second Apply, and asserts only exit codes, which links exist and where they point, and idempotence. The same seam covers conflict refusal, a public clone with no private companion, and the private environment loading when the private companion exists. The existing static seam is `bake lint`.
- **Apply.**
    - Apply calls the tool manager's dotfile apply without force and without a skip-confirmation flag, so behavior is identical locally and in CI.
    - On a conflict it exits non-zero and prints the resolution message. No force option is added to `bake`.
    - Verified behavior (tool manager 2026.11.12, throwaway HOME): clean machine links everything and exits 0 with no prompt; a rerun reports everything applied; an existing regular file is refused with the file named and left untouched; a symlink pointing elsewhere is silently replaced.
- **Private groups (ADR 0001).** The three private groups move from the base config into a separate environment config in the public repo root. Apply passes the private environment flag only when the private companion's source directory exists. Verified: with the private groups moved out, a public clone without `private/` applies and exits 0. Loading with the flag was observed to read the environment config and attempt the private groups. The full run with a complete `private/` (done in ticket 01) first failed: public and private both linked `~/.ssh/config`, and mise rejects two groups on one target. The private copy was a duplicate and was removed from the private repo; the full run then links all public and private groups (`bake test-integration`).
- **Tools and apps (ADR 0002).** The tool manager installs every command-line tool at `latest`, pinned by hand only when a release breaks one; no lockfile. macOS GUI apps come from a public Brewfile and a private Brewfile, casks only, applied on macOS only, never with cleanup. The default platform-tools step of the shared Setup is kept on macOS and reduced to the tool manager elsewhere. No Brewfile lock is written. A tool lives in exactly one of the two.
- **Times.** Four times: Apply, Setup (installs; does not upgrade mise tools; for now also upgrades Homebrew through the shared bake library, until nothing there is installed by hand), Update (new, on demand: upgrades tool-manager tools and Brewfile apps) and Use. Whether the shared bake library already offers an Update command, or this repo writes it, is unverified and is checked first.
- **Assert.** Apply ends with an Assert that Use will succeed. The hand-written check is replaced by the shared bake asserts for the age key and bootstrap secrets, plus one repo-specific assert that each declared secret resolves. Messages say what is missing and nothing about how to fix it: the fix depends on how the user got there, and hints proved hard to keep correct. All uses of "preflight" in code, docs and wiki are renamed (already done in the working tree for docs and the current code; the replacement with shared asserts remains).
- **Secrets in CI.** A CI-only secret-store project holds dummy values under the same names as the real project. A secrets profile for CI overrides the provider's project, and the CI environment sets that profile and a machine-account token (scoped to only that project) from a repository secret. Verified: the secrets tool supports profiles. Verified (ticket 04, fnox 1.50.0): a profile can override a provider's project id. `[profiles.ci.providers.bw]` with its own `project_id` makes `fnox -P ci` call `bws` with the override, while top-level secrets still resolve; no second provider block is needed. Verified (ticket 04): Setup creates the age key without a human, but the bootstrap token only comes from a terminal, so with no TTY Setup skipped it and the Assert failed. No code change is needed: the CI job runs `bake setup-fnox` (age key, token skipped without a terminal) then `bake secret set FNOX_BWS_ACCESS_TOKEN`, as a person would; in a throwaway HOME with no TTY this cached the token, with the value in no plaintext file, and later steps need no token in their environment.
- **CI, public.** Workflows for CI orchestration, pre-commit and lint, security (vulnerability scan and secret scan, daily and on push), pull request title check, versioning and tagging (no publish step), the Fresh-machine job, and a dependency-update config. The Fresh-machine job runs the full Setup including the Brewfile apps, on macOS and Linux with fail-fast off; Linux is commented out with a TODO if it fails. It checks out no submodules and uses the dummy-secrets profile. Actions are pinned by SHA with the version in a comment, with minimal permissions. The CI shape follows the bakefile repo.
- **CI, private.** The same set, using its own bake space. Its Fresh-machine job checks out public at main, places private at the private path, and runs the combined path with the private environment flag and the dummy-secrets profile; it also runs weekly.
- **Versioning.** Both repos use the same release-and-tag flow as the bakefile repo (semantic release plus version tags), without publishing. The public tag pins the private pointer.
- **Docs and tracker.** Add a license (matching the bakefile repo), a contributing guide, the three agent docs (issue tracker, triage labels, domain), the agent-skills section of the steering file, a fuller README, and updated glossary and ADRs. The tracker is local markdown in `.tracker/<feature>/`, committed, with GitHub Issues only on request; this spec is the first entry.
- **Sequencing.** Verify the unverified items first (the full private environment run, the secrets profile override, non-interactive Setup, and the Update command), then Apply and private groups, tools and Brewfile, Assert, CI, docs, then the per-tool config decisions and the final scans.

## Testing Decisions

- A good test here observes external behavior only: exit codes, filesystem links and their targets, and idempotence on a rerun. It never asserts on internal function calls or log wording beyond the named file.
- Tested through the one seam above: the Fresh-machine path in a throwaway HOME locally and in the Fresh-machine job in CI, covering clean apply, rerun, conflict refusal with the file untouched, public-only clone, and private environment loading.
- Public CI: public repo alone, macOS and Linux. Private CI: combined public and private, macOS and Linux when Linux passes, where logs are private.
- Static checks stay in `bake lint`: shell lint, workflow and docs formatting, Brewfile syntax, secret scan.
- Not tested in CI: adoption of hand-installed apps (a clean runner has none; verified once by hand), real secrets, and anything that needs a real new machine; one real new-machine run is a v1 gate item.
- Prior art: the existing shell-lint step of `bake lint` and the manual throwaway-HOME runs used to verify Apply behavior. There are no automated tests in the repo yet.

## Out of Scope

- macOS `defaults` and other system settings.
- A machine-local override mechanism (a fifth home).
- An uninstall or rollback command.
- Linux bootstrap beyond the CI job, other platforms, and Windows.
- A package manifest for anything other than macOS GUI apps.
- Publishing releases or packages.
- Moving agent-home's linked files into dotfiles.
- Per-tool config for starship, zed, git, gh, yt-dlp and marimo, and the Colima removal: tracked in the planning notes, not part of this spec's tickets, except the rule that each gets a public, private or disposable decision before v1.

## Further Notes

- v1 gate: a fresh machine passes `mise install`, `bake setup-dev` and `bake apply`, proven by CI plus one real new-machine run; Apply is idempotent and never overwrites unmanaged files; both repos' history scans clean; every tool has a home; CI, license, dependency updates and agent docs exist.
- Two earlier commits and the working-tree changes (glossary, ADRs, the assert rename) are unpushed; nothing here is landed. Landing order is private first, then the public submodule pointer, then public, each step only when named.
- The cost of public CI is macOS runner minutes; measure the first Fresh-machine run before adding caches or opt-outs.
