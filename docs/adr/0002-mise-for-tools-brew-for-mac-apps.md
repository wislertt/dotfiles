# mise installs tools; Homebrew installs only macOS GUI apps, from a Brewfile

Every command-line tool comes from mise, so Setup is the same on any platform. GUI apps (Orca, Zed, Docker) are macOS casks that mise cannot install, so they live in a `Brewfile`, applied only on macOS, and never with `brew bundle --cleanup` because that would remove apps installed by hand. A tool lives in exactly one of the two. We considered mise-only with a manual "install by hand" list (rejected: apps would be unreproducible) and Brewfile for everything (rejected: it ties the whole setup to Homebrew).

Casks float, so `Brewfile.lock.json` is not written, and mise tools are pinned and bumped by Renovate. Setup installs only what is missing; Update upgrades.
