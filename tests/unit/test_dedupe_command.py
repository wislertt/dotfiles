from pathlib import Path
from unittest.mock import patch

import pytest

from src.python import bakefile
from tests.unit.conftest import FakeCtx


@pytest.fixture(autouse=True)
def managers_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bakefile.shutil, "which", lambda name: f"/usr/bin/{name}")


@pytest.fixture
def declared_jq(fake_repo: Path, fake_ctx: FakeCtx) -> Path:
    (fake_repo / "mise.toml").write_text('[tools]\njq = "latest"\n')
    fake_ctx.stdout["brew leaves"] = "jq\nbat\n"
    return fake_repo


def _uninstalls(fake_ctx: FakeCtx) -> list[list[str]]:
    return [c for c in fake_ctx.commands if "uninstall" in c]


def test_dedupe_without_yes_lists_and_removes_nothing(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, declared_jq: Path
) -> None:
    del declared_jq
    with patch.object(bakefile.console, "echo") as echo:
        bakebook.dedupe(yes=False)
    assert _uninstalls(fake_ctx) == []
    assert [c.args[0] for c in echo.call_args_list] == ["brew: jq"]


@pytest.mark.usefixtures("declared_jq")
def test_dedupe_with_yes_removes_only_the_declared_duplicate(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx
) -> None:
    bakebook.dedupe(yes=True)
    assert _uninstalls(fake_ctx) == [["brew", "uninstall", "--formula", "jq"]]


def test_dedupe_leaves_a_declared_tool_alone_until_mise_has_it(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, declared_jq: Path
) -> None:
    del declared_jq
    fake_ctx.failing.add("mise where jq")  # not installed yet
    bakebook.dedupe(yes=True)
    assert _uninstalls(fake_ctx) == []


def test_dedupe_never_removes_a_brewfile_cask_it_just_installed(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    (fake_repo / "src" / "lib" / "Brewfile").write_text('cask "zed"\n')
    fake_ctx.stdout["brew list --cask -1"] = "zed\n"
    bakebook.dedupe(yes=True)
    assert _uninstalls(fake_ctx) == []


def test_dedupe_checks_mise_with_the_declared_key_not_the_bare_name(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    (fake_repo / "mise.toml").write_text('[tools]\n"npm:oxfmt" = "latest"\n')
    fake_ctx.stdout["npm ls -g --depth=0 --json"] = '{"dependencies": {"oxfmt": {}}}'
    fake_ctx.failing.add("mise where oxfmt")  # the bare name would resolve nothing
    bakebook.dedupe(yes=True)
    assert ["mise", "where", "npm:oxfmt"] in fake_ctx.commands
    assert _uninstalls(fake_ctx) == [["npm", "uninstall", "-g", "oxfmt"]]


def test_dedupe_keeps_a_cask_when_its_mise_copy_is_missing(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    (fake_repo / "mise.toml").write_text('[tools]\nzed = "latest"\n')
    (fake_repo / "src" / "lib" / "Brewfile").write_text('cask "zed"\n')
    fake_ctx.stdout["brew list --cask -1"] = "zed\n"
    fake_ctx.failing.add("mise where zed")
    bakebook.dedupe(yes=True)
    assert _uninstalls(fake_ctx) == []


def test_dedupe_names_what_a_manager_refused(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, declared_jq: Path
) -> None:
    del declared_jq
    fake_ctx.failing.add("brew uninstall --formula jq")
    with patch.object(bakefile.console, "warning") as warning:
        bakebook.dedupe(yes=True)
    assert "brew: jq" in warning.call_args.args[0]
