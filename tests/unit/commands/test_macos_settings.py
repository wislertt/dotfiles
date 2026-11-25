from pathlib import Path

import pytest
import typer
from bake.utils.settings import PlatformType

from src.python import bakefile
from src.python.commands import setup_update
from tests.unit.conftest import FakeCtx


@pytest.fixture(autouse=True)
def state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    state = tmp_path / "state"
    monkeypatch.setenv("XDG_STATE_HOME", str(state))
    monkeypatch.setattr(setup_update.shutil, "which", lambda name: f"/bin/{name}")
    return state


def _script(root: Path, name: str, body: str = "true\n", private: bool = False) -> Path:
    folder = (root / "private" if private else root) / "src" / "lib" / "macos"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(body)
    return folder / name


def _ran(fake_ctx: FakeCtx) -> list[str]:
    return [Path(c[1]).name for c in fake_ctx.commands if c[0] == "bash"]


@pytest.fixture
def scripts(fake_repo: Path) -> Path:
    _script(fake_repo, "keyboard.sh")
    _script(fake_repo, "dock.sh")
    _script(fake_repo, "trackpad.sh", private=True)
    return fake_repo


@pytest.mark.parametrize("step", ["_setup_platform_tools", "_update_platform_tools"])
def test_each_settings_script_runs_public_then_private_on_macos(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, scripts: Path, step: str
) -> None:
    del scripts
    getattr(bakebook, step)("macos")
    assert _ran(fake_ctx) == ["dock.sh", "keyboard.sh", "trackpad.sh"]


def test_an_unchanged_script_does_not_run_again(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, scripts: Path
) -> None:
    del scripts
    bakebook._setup_platform_tools("macos")
    fake_ctx.commands.clear()
    bakebook._update_platform_tools("macos")
    assert _ran(fake_ctx) == []


def test_only_a_changed_script_runs_again(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, scripts: Path
) -> None:
    bakebook._setup_platform_tools("macos")
    fake_ctx.commands.clear()
    _script(scripts, "trackpad.sh", "defaults write x y -bool true\n", private=True)
    bakebook._setup_platform_tools("macos")
    assert _ran(fake_ctx) == ["trackpad.sh"]


def test_a_failed_script_runs_again_next_time(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    dock = _script(fake_repo, "dock.sh")
    fake_ctx.failing.add(f"bash {dock}")
    with pytest.raises(typer.Exit):
        bakebook._setup_platform_tools("macos")
    fake_ctx.failing.clear()
    fake_ctx.commands.clear()
    bakebook._setup_platform_tools("macos")
    assert _ran(fake_ctx) == ["dock.sh"]


@pytest.mark.parametrize("platform", ["linux", "windows"])
def test_no_settings_script_runs_off_macos(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    scripts: Path,
    platform: PlatformType,
) -> None:
    del scripts
    bakebook._setup_platform_tools(platform)
    assert _ran(fake_ctx) == []


def test_files_that_are_not_shell_scripts_are_ignored(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    _script(fake_repo, "dock.sh")
    _script(fake_repo, "README.md")
    bakebook._setup_platform_tools("macos")
    assert _ran(fake_ctx) == ["dock.sh"]
