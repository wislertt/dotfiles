from pathlib import Path

import pytest
from bake.utils.settings import PlatformType

from src.python import bakefile
from tests.unit.conftest import FakeCtx


def _bundles(fake_ctx: FakeCtx) -> list[list[str]]:
    return [c for c in fake_ctx.commands if c[:2] == ["brew", "bundle"]]


@pytest.fixture(autouse=True)
def brew_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bakefile.shutil, "which", lambda _name: "/opt/homebrew/bin/brew"
    )


@pytest.fixture
def brewfiles(fake_repo: Path) -> Path:
    (fake_repo / "src" / "lib" / "Brewfile").write_text('cask "zed"\n')
    (fake_repo / "private" / "src" / "lib").mkdir(parents=True)
    (fake_repo / "private" / "src" / "lib" / "Brewfile").write_text(
        'cask "docker-desktop"\n'
    )
    return fake_repo


def test_setup_installs_each_brewfile_on_macos(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path
) -> None:
    bakebook._setup_platform_tools("macos")
    files = [c[c.index("--file") + 1] for c in _bundles(fake_ctx)]
    assert files == [
        str(brewfiles / "src" / "lib" / "Brewfile"),
        str(brewfiles / "private" / "src" / "lib" / "Brewfile"),
    ]


def test_setup_skips_a_missing_private_brewfile(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    (fake_repo / "src" / "lib" / "Brewfile").write_text('cask "zed"\n')
    bakebook._setup_platform_tools("macos")
    assert len(_bundles(fake_ctx)) == 1


@pytest.mark.parametrize("platform", ["linux", "windows"])
def test_setup_runs_no_brew_off_macos(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    brewfiles: Path,
    platform: PlatformType,
) -> None:
    del brewfiles
    bakebook._setup_platform_tools(platform)
    assert _bundles(fake_ctx) == []


@pytest.mark.parametrize("step", ["_setup_platform_tools", "_update_platform_tools"])
def test_platform_step_runs_only_the_brewfiles(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path, step: str
) -> None:
    # Homebrew holds only what the Brewfiles declare, so no blanket `brew upgrade`
    del brewfiles
    getattr(bakebook, step)("macos")
    assert fake_ctx.commands == _bundles(fake_ctx)
    assert len(fake_ctx.commands) == 2


def test_setup_tools_never_upgrade(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    del fake_repo
    bakebook._setup_tools()
    assert fake_ctx.commands
    assert not [c for c in fake_ctx.commands if "upgrade" in c]


def test_update_upgrades_each_brewfile_on_macos(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path
) -> None:
    bakebook._update_platform_tools("macos")
    bundles = _bundles(fake_ctx)
    assert [c[c.index("--file") + 1] for c in bundles] == [
        str(brewfiles / "src" / "lib" / "Brewfile"),
        str(brewfiles / "private" / "src" / "lib" / "Brewfile"),
    ]
    assert all(c[2] == "upgrade" for c in bundles)


def test_update_runs_no_brew_off_macos(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path
) -> None:
    del brewfiles
    bakebook._update_platform_tools("linux")
    assert _bundles(fake_ctx) == []


def test_setup_fails_clearly_without_homebrew(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    brewfiles: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del brewfiles
    monkeypatch.setattr(bakefile.shutil, "which", lambda _name: None)
    with pytest.raises(SystemExit, match="Homebrew"):
        bakebook._setup_platform_tools("macos")
    assert _bundles(fake_ctx) == []


def test_setup_survives_an_unreachable_private_submodule(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx
) -> None:
    fake_ctx.returncode = 1
    bakebook._sync_submodules(frozen=True)
    assert ["git", "submodule", "update"] == fake_ctx.commands[0][:3]
