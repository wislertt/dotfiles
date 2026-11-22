from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar, cast

from bake import command, console
from bakelib.refreshable_cache import FetchFn, FnoxFetchFn
from bakelib.refreshable_cache.fnox import run_fnox
from bakelib.space import FnoxSpace, PythonSpace, SubmodulesUtils
from bakelib.space.params import DurationsOption

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

    __exclude_command_methods__: ClassVar[list[str]] = [
        "test",
        "test_all",
        "test_integration",
    ]

    def _lint_fast(self) -> None:
        super()._lint_fast()
        self._assert_global_fnox_empty()

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
        # last step, so the preflight runs once the age key and token exist
        self._apply(in_setup=True)

    @command()
    def apply(self) -> None:
        """Link dotfiles into ~ with mise (overwrites existing files), then check use-time needs"""
        self._apply()

    def _apply(self, *, in_setup: bool = False) -> None:
        self.ctx.run("mise dotfiles apply --force")
        self._preflight(in_setup=in_setup)

    def _preflight(self, *, in_setup: bool) -> None:
        # Read-only: reports names only, never values, and writes nothing
        problems: list[str] = []
        if not self._age_key_file().exists():
            problems.append(f"age key not found: {self._age_key_file()}")
        else:
            vault = self.vault()
            for name in self.fnox_bootstrap_secrets:
                if not vault.has_value(name):
                    problems.append(f"{name} not stored")
            if not problems:
                problems.extend(
                    f"secret {key} does not resolve"
                    for key in SECRET_KEYS
                    if not self._secret_resolves(key)
                )
        if problems:
            for problem in problems:
                console.error(problem)
            # setup-dev already ran the setup steps, so pointing back at it would loop
            hint = (
                "fix the items above (rerun `bake setup-fnox`, or check the Bitwarden token and secret names)"
                if in_setup
                else "run `bake setup-dev`"
            )
            console.error(f"Preflight failed: {hint}")
            raise SystemExit(1)
        console.success("Preflight passed")

    def _secret_resolves(self, key: str) -> bool:
        if self.vault().has_value(key):
            return True
        # not cached yet (fresh Mac): ask fnox directly, which does not write the cache
        return run_fnox(["--no-daemon", "get", key]).returncode == 0

    def test(self, durations: DurationsOption = None) -> None:
        # assert-setup-dev calls test(); a dotfiles repo has nothing to test
        del durations


bakebook = MyBakebook()
