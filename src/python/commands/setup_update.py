import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from bake import Context, console
from bake.utils.settings import PlatformType
from bakelib.space import SubmodulesUtils

from src.python.core import brewfiles, repo, signing


def _git(ctx: Context, path: Path, *args: str) -> str:
    return ctx.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        stream=False,
        echo=False,
        check=False,
    ).stdout.strip()


def _brew_env() -> dict[str, str]:
    """Lets a cask's sudo ask in a dialog, since bake runs it without a terminal, and adopts an app already installed."""
    env: dict[str, str] = {}
    if not os.environ.get("SUDO_ASKPASS"):
        env["SUDO_ASKPASS"] = str(repo.ROOT / "src/lib/sudo-askpass")
    opts = os.environ.get("HOMEBREW_CASK_OPTS", "").split()
    env["HOMEBREW_CASK_OPTS"] = " ".join(
        opts if "--adopt" in opts else [*opts, "--adopt"]
    )
    return env


class SetupUpdateMixin(SubmodulesUtils):
    if TYPE_CHECKING:
        # ApplyMixin, MacosSettingsMixin and MachineMixin provide them in the bakebook
        def _apply(self) -> None: ...
        def _macos_settings(self, platform: PlatformType) -> None: ...
        def _roles(self) -> list[str]: ...
        def _machine_name(self) -> str: ...
        def _name_this_machine(self) -> str: ...

    def _brew_bundle(self, platform: PlatformType, verb: str) -> None:
        if platform != "macos":
            return
        found = brewfiles.paths(repo.ROOT, self._roles())
        if found and not shutil.which("brew"):
            raise SystemExit(
                "Homebrew is not installed, so the Brewfile apps cannot be set up"
            )
        failed = [
            brewfile
            for brewfile in found
            if self.ctx.run(
                ["brew", "bundle", verb, "--file", str(brewfile)],
                env=_brew_env(),
                check=False,
            ).returncode
        ]
        if failed:
            raise SystemExit(
                "brew bundle failed for "
                + ", ".join(str(f.relative_to(repo.ROOT)) for f in failed)
            )

    # No super(): bakelib's default runs a blanket `brew upgrade`, and Homebrew holds only the Brewfiles
    def _setup_platform_tools(self, platform: PlatformType) -> None:
        self._brew_bundle(platform, "install")
        self._macos_settings(platform)

    def _update_platform_tools(self, platform: PlatformType) -> None:
        self._brew_bundle(platform, "upgrade")
        if platform == "macos" and shutil.which("brew"):
            self.ctx.run(["brew", "cleanup"])
        self._macos_settings(platform)

    def _private_work_in_progress(self) -> str | None:
        private = repo.ROOT / "private"
        if not (private / ".git").exists():
            return None
        if _git(self.ctx, private, "status", "--porcelain"):
            return "uncommitted changes"
        branch = _git(self.ctx, private, "symbolic-ref", "--quiet", "--short", "HEAD")
        if branch and branch != "main":
            return f"branch {branch} checked out"
        ahead = _git(self.ctx, private, "rev-list", "--count", "origin/main..HEAD")
        if ahead not in ("", "0"):
            return f"{ahead} commits not on origin/main"
        return None

    def _sync_submodules(self, frozen: bool = False) -> None:
        # a sync detaches private at the pinned commit, which strands work in progress there
        if reason := self._private_work_in_progress():
            console.warning(f"Skipping submodule sync, private/ has {reason}")
            return
        # the public repo must work alone, so an unreachable private companion is not fatal
        try:
            super()._sync_submodules(frozen=frozen)
        except typer.Exit:
            console.warning(
                "Private companion not available, continuing with public only"
            )

    def _setup_tools(self) -> None:
        # bakelib's default ends with `mise upgrade` and `uv python upgrade`; those belong to Update
        self._add_mise_tools()
        self.ctx.run(["mise", "install"])
        self.ctx.run(["mise", "doctor"])
        self.ctx.run(["mise", "list", "--local"])
        self._sync_submodules(frozen=True)

    def _update_tools(self) -> None:
        super()._update_tools()
        self.ctx.run(["mise", "prune", "--yes"])  # bake runs it without a terminal
        self.ctx.run(["uv", "cache", "prune"])

    def _get_mise_tools(self) -> set[str]:
        return {
            *super()._get_mise_tools(),
            "bitwarden-secrets-manager",
            "jq",
            "shellcheck",
        }

    def _get_required_cli_tools(self) -> dict[str, set[Path] | None]:
        tools = super()._get_required_cli_tools()
        tools["bws"] = None  # fnox shells out to it for every Bitwarden secret
        tools["jq"] = None
        tools["shellcheck"] = None
        return tools

    def _assert_tools(self) -> None:
        super()._assert_tools()
        # bakelib only prints a missing tool; the assert must fail so CI goes red
        missing = [
            name
            for name in self._get_required_cli_tools()
            if not self.ctx.dry_run and shutil.which(name) is None
        ]
        if missing:
            console.error(f"required tools missing: {', '.join(missing)}")
            raise SystemExit(1)

    def _setup_project(self) -> None:
        super()._setup_project()
        self._setup_dotfiles()

    def _update_project(self) -> None:
        super()._update_project()
        self._update_dotfiles()

    def _setup_dotfiles(self) -> None:
        """This repo's own Setup steps, in order, after bakelib's."""
        # before the key, so the assert runs once the age key and token exist
        self._apply()
        if self.ctx.dry_run:
            return
        name = self._name_this_machine()
        signing.SigningKey.for_this_machine(self.ctx, name).sync(create=True)

    def _update_dotfiles(self) -> None:
        """This repo's own Update steps, in order, after bakelib's."""
        if self.ctx.dry_run:
            return
        name = self._machine_name()
        signing.SigningKey.for_this_machine(self.ctx, name).sync(create=False)
