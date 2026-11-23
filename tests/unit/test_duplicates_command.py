from pathlib import Path
from unittest.mock import patch

import pytest

from src.python import bakefile
from tests.unit.conftest import FakeCtx


def _exe(directory: Path, name: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text("")
    (directory / name).chmod(0o755)
    return directory


@pytest.fixture
def machine(
    fake_repo: Path,
    fake_ctx: FakeCtx,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Path]:
    """jq declared in mise, with a Homebrew copy and a mise shim on PATH."""
    (fake_repo / "mise.toml").write_text('[tools]\njq = "latest"\n')
    dirs = {
        "mise": _exe(tmp_path / "mise" / "installs" / "jq", "jq"),
        "shims": _exe(tmp_path / "mise" / "shims", "jq"),
        "brew": _exe(tmp_path / "brew", "jq"),
    }
    monkeypatch.setenv("PATH", ":".join(str(d) for d in dirs.values()))
    fake_ctx.stdout["mise bin-paths jq"] = f"{dirs['mise']}\n"
    return dirs


def _lines(echo) -> list[str]:
    return [c.args[0] for c in echo.call_args_list]


def test_duplicates_reports_a_copy_outside_mise_and_changes_nothing(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, machine: dict[str, Path]
) -> None:
    with patch.object(bakefile.console, "echo") as echo:
        bakebook.duplicates()
    assert _lines(echo) == [f"jq: {machine['brew'] / 'jq'}"]
    assert [c[0] for c in fake_ctx.commands] == ["mise"]  # only `mise bin-paths`


def test_duplicates_ignores_the_mise_shims(
    bakebook: bakefile.MyBakebook, machine: dict[str, Path]
) -> None:
    with patch.object(bakefile.console, "echo") as echo:
        bakebook.duplicates()
    assert not any("shims" in line for line in _lines(echo))


def test_a_declared_tool_mise_has_not_installed_is_not_reported(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, machine: dict[str, Path]
) -> None:
    del machine
    fake_ctx.failing.add("mise bin-paths jq")
    with patch.object(bakefile.console, "echo") as echo:
        bakebook.duplicates()
    assert _lines(echo) == []


def test_duplicates_says_so_when_there_are_none(
    bakebook: bakefile.MyBakebook, machine: dict[str, Path]
) -> None:
    (machine["brew"] / "jq").unlink()
    with patch.object(bakefile.console, "success") as success:
        bakebook.duplicates()
    assert success.call_args.args[0] == "No duplicates"


def test_a_project_virtualenv_is_not_an_install(
    bakebook: bakefile.MyBakebook,
    machine: dict[str, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    venv = _exe(tmp_path / "project" / ".venv" / "bin", "jq")
    monkeypatch.setenv("PATH", f"{machine['mise']}:{venv}")
    with patch.object(bakefile.console, "echo") as echo:
        bakebook.duplicates()
    assert _lines(echo) == []
