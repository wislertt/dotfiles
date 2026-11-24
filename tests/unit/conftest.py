from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import PropertyMock, patch

import pytest
import typer

from src.python import bakefile


class FakeCtx:
    """Stands in for the bake command context: records commands, runs none."""

    def __init__(
        self, returncode: int = 0, stdout: dict[str, str] | None = None
    ) -> None:
        self.returncode = returncode
        self.stdout = (
            stdout or {}
        )  # canned output, keyed by the command joined with spaces
        self.failing: set[str] = set()  # commands (joined with spaces) that exit 1
        self.dry_run = False
        self.commands: list[list[str]] = []
        self.envs: list[dict[str, str]] = []

    def run(self, cmd: list[str] | str, **kwargs: Any) -> SimpleNamespace:
        self.commands.append(cmd.split() if isinstance(cmd, str) else cmd)
        self.envs.append(kwargs.get("env") or {})
        key = " ".join(self.commands[-1])
        returncode = 1 if key in self.failing else self.returncode
        if kwargs.get("check", True) and returncode:
            raise typer.Exit(returncode)  # like bake, raising on failure by default
        return SimpleNamespace(
            returncode=returncode, stdout=self.stdout.get(key, ""), stderr=""
        )


class FakeVault:
    """Stands in for the secret cache, so no test reads the real fnox cache or keychain."""

    def __init__(self) -> None:
        self.values: set[str] = set()

    def has_value(self, key: str) -> bool:
        return key in self.values


@pytest.fixture
def fake_vault() -> FakeVault:
    return FakeVault()


@pytest.fixture
def fake_ctx() -> FakeCtx:
    return FakeCtx()


@pytest.fixture
def bakebook(fake_ctx: FakeCtx, fake_vault: FakeVault) -> Iterator[bakefile.MyBakebook]:
    with (
        patch.object(bakefile.MyBakebook, "ctx", new_callable=PropertyMock) as ctx,
        patch.object(bakefile.MyBakebook, "vault", return_value=fake_vault),
    ):
        ctx.return_value = fake_ctx
        book = bakefile.MyBakebook()
        fake_ctx.commands.clear()  # construction runs its own setup commands
        fake_ctx.envs.clear()
        yield book


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repo root without the private companion; bakefile finds it through `__file__`."""
    monkeypatch.setattr(
        bakefile, "__file__", str(tmp_path / "src" / "python" / "bakefile.py")
    )
    (tmp_path / "src" / "lib").mkdir(parents=True)
    return tmp_path
