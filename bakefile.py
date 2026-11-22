from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, cast
from unittest.mock import patch

from bake import command, console
from bakelib.refreshable_cache import FetchFn, FnoxFetchFn
from bakelib.refreshable_cache.fnox import run_fnox
from bakelib.space import FnoxSpace, PythonSpace, SubmodulesUtils
from bakelib.space import fnox as fnox_space
from identify import identify

# Names the scripts in src/bin read with `bake secret get`; the references live in fnox.toml
SECRET_KEYS = ("CLAUDE_GLM_AUTH_TOKEN", "AICLIENT2API_API_KEY")


class MyBakebook(SubmodulesUtils, FnoxSpace[str | None], PythonSpace):
    fnox_bootstrap_secrets: ClassVar[Mapping[str, str]] = {
        "FNOX_BWS_ACCESS_TOKEN": "Bitwarden access token",
    }

    def get_secret_fetch_fns(self) -> tuple[FetchFn[str | None], ...]:
        return (
            *super().get_secret_fetch_fns(),
            *(cast("FetchFn[str | None]", FnoxFetchFn(key)) for key in SECRET_KEYS),
        )

    def _get_mise_tools(self) -> set[str]:
        return {*super()._get_mise_tools(), "jq", "shellcheck"}

    def _get_required_cli_tools(self) -> dict[str, set[Path] | None]:
        tools = super()._get_required_cli_tools()
        tools["jq"] = None
        tools["shellcheck"] = None
        return tools

    def _test(
        self,
        *,
        tests_paths: str | list[str],
        durations: int | None = None,
        verbose: bool = False,
        **_ignored: Any,
    ) -> None:
        # bakelib's coverage points at src/, which holds no Python here
        super()._test(
            tests_paths=tests_paths,
            durations=durations,
            verbose=verbose,
            coverage_report=False,
        )

    def _lint_fast(self) -> None:
        super()._lint_fast()
        self._lint_shell()
        self._assert_global_fnox_empty()

    def _lint_shell(self) -> None:
        # Same file types as the pre-commit shellcheck hook; ShellCheck cannot parse zsh, so `zsh -n`
        out = self.ctx.run(
            ["git", "ls-files", "-z"], capture_output=True, stream=False, echo=False
        ).stdout
        tags = {
            name: identify.tags_from_path(name)
            for name in filter(None, out.split("\0"))
            if Path(name).is_file() and not Path(name).is_symlink()
        }
        sh = [n for n, t in tags.items() if "shell" in t and "zsh" not in t]
        zsh = [n for n, t in tags.items() if "zsh" in t]
        if sh:
            self.ctx.run(["shellcheck", "--", *sh])
        for name in zsh:
            self.ctx.run(["zsh", "-n", name])

    def _assert_global_fnox_empty(self) -> None:
        # Secrets come only from `bake secret get`; the global fnox config must stay unused
        path = Path.home() / ".config" / "fnox" / "config.toml"
        if not path.exists():
            return
        # fnox exits 0 either way, so judge by output
        secrets = self._fnox_out("list", "-c", str(path))
        providers = self._fnox_out("provider", "list", "-c", str(path))
        if providers or not secrets.startswith("No secrets defined"):
            raise SystemExit(f"Global fnox config is not empty: {path}. Clear it.")

    def _fnox_out(self, *args: str) -> str:
        cmd = ["fnox", "--no-color", "--no-daemon", *args]
        return self.ctx.run(
            cmd, capture_output=True, stream=False, echo=False
        ).stdout.strip()

    def _setup_project(self) -> None:
        super()._setup_project()
        # last step, so the assert runs once the age key and token exist
        self._apply()

    @command()
    def apply(self) -> None:
        """Link dotfiles into ~ with mise (never overwrites a regular file), then assert use-time needs"""
        self._apply()

    def _apply(self) -> None:
        self._run_mise_dotfiles_apply()
        self._assert_dotfiles_readiness()

    def _run_mise_dotfiles_apply(self) -> None:
        # No --force and no --yes: a conflicting regular file makes mise exit non-zero
        cmd = ["mise", "dotfiles", "apply"]
        if (Path(__file__).parent / "private" / "src").is_dir():
            cmd[1:1] = ["-E", "private"]
        if self.ctx.run(cmd, check=False).returncode != 0:
            console.error(
                "Apply failed. If the output above names files that already exist and are not managed, "
                "move or delete each one, then rerun `bake apply`. "
                "To overwrite on purpose, run `mise dotfiles apply --force` yourself (not via bake)."
            )
            raise SystemExit(1)

    def _assert_dotfiles_readiness(self) -> None:
        # Read-only: reports names only, never values, and writes nothing
        failures = self._bakelib_assert_failures()
        if not failures:
            failures = self._unresolved_secret_failures()
        if failures:
            for failure in failures:
                console.error(failure)
            console.error("Assert failed")
            raise SystemExit(1)
        console.success("Assert passed")

    def _bakelib_assert_failures(self) -> list[str]:
        # bakelib's asserts only print, so collect what they report
        failures: list[str] = []
        with (
            patch.object(fnox_space.console, "error", side_effect=failures.append),
            patch.object(fnox_space.console, "cmd"),
        ):
            self._assert_age_key()
            self._assert_bootstrap_secrets()
        return failures

    def _unresolved_secret_failures(self) -> list[str]:
        return [
            f"secret {key} does not resolve"
            for key in SECRET_KEYS
            if not self._secret_resolves(key)
        ]

    def _secret_resolves(self, key: str) -> bool:
        if self.vault().has_value(key):
            return True
        # not cached yet (fresh Mac): ask fnox directly, which does not write the cache
        return run_fnox(["--no-daemon", "get", key]).returncode == 0


bakebook = MyBakebook()
