from pathlib import Path

import pytest
from bake.utils.settings import PlatformType

from src.python import bakefile
from src.python.commands import setup_update
from tests.unit.conftest import FakeCtx


def _bundles(fake_ctx: FakeCtx) -> list[list[str]]:
    return [c for c in fake_ctx.commands if c[:2] == ["brew", "bundle"]]


@pytest.fixture(autouse=True)
def brew_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        setup_update.shutil, "which", lambda _name: "/opt/homebrew/bin/brew"
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
def test_platform_step_runs_no_blanket_brew_upgrade(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path, step: str
) -> None:
    # Homebrew holds only what the Brewfiles declare, so no blanket `brew upgrade`
    del brewfiles
    getattr(bakebook, step)("macos")
    assert len(_bundles(fake_ctx)) == 2
    assert fake_ctx.commands == _bundles(fake_ctx) + _removals(fake_ctx)


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
    monkeypatch.setattr(setup_update.shutil, "which", lambda _name: None)
    with pytest.raises(SystemExit, match="Homebrew"):
        bakebook._setup_platform_tools("macos")
    assert _bundles(fake_ctx) == []


def test_setup_survives_an_unreachable_private_submodule(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    del fake_repo
    fake_ctx.returncode = 1
    bakebook._sync_submodules(frozen=True)
    assert _synced(fake_ctx)


def _private_git(root: Path, *args: str) -> str:
    return " ".join(["git", "-C", str(root / "private"), *args])


@pytest.fixture
def private_checkout(fake_repo: Path) -> Path:
    (fake_repo / "private").mkdir()
    (fake_repo / "private" / ".git").write_text("gitdir: ../.git/modules/private\n")
    return fake_repo


def _synced(fake_ctx: FakeCtx) -> bool:
    return any(c[:3] == ["git", "submodule", "update"] for c in fake_ctx.commands)


def test_sync_runs_when_private_is_clean_on_main(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, private_checkout: Path
) -> None:
    fake_ctx.stdout[
        _private_git(private_checkout, "symbolic-ref", "--quiet", "--short", "HEAD")
    ] = "main\n"
    fake_ctx.stdout[
        _private_git(private_checkout, "rev-list", "--count", "origin/main..HEAD")
    ] = "0\n"
    bakebook._sync_submodules()
    assert _synced(fake_ctx)


def test_sync_runs_without_a_private_checkout(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, fake_repo: Path
) -> None:
    del fake_repo
    bakebook._sync_submodules()
    assert _synced(fake_ctx)


@pytest.mark.parametrize(
    ("args", "stdout"),
    [
        (("status", "--porcelain"), " M AGENTS.md\n"),
        (("symbolic-ref", "--quiet", "--short", "HEAD"), "feat/steering-file\n"),
        (("rev-list", "--count", "origin/main..HEAD"), "2\n"),
    ],
    ids=["uncommitted", "feature-branch", "unpushed"],
)
def test_sync_skips_private_work_in_progress(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    private_checkout: Path,
    args: tuple[str, ...],
    stdout: str,
) -> None:
    fake_ctx.stdout[_private_git(private_checkout, *args)] = stdout
    bakebook._sync_submodules(frozen=True)
    assert not _synced(fake_ctx)


IOREG = '    "IOPlatformSerialNumber" = "SERIAL0001"\n'


@pytest.mark.parametrize("serial", ["SERIAL0001", "SOMEONE-ELSE"])
@pytest.mark.parametrize("step", ["_setup_platform_tools", "_update_platform_tools"])
def test_a_role_brewfile_is_used_only_on_a_machine_with_that_role(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    brewfiles: Path,
    step: str,
    serial: str,
) -> None:
    lib = brewfiles / "private" / "src" / "lib"
    (lib / "machines.toml").write_text(
        f'"{serial}" = {{ name = "work-mac", roles = ["work"] }}\n'
    )
    (lib / "Brewfile.work").write_text('cask "microsoft-teams"\n')
    fake_ctx.stdout["ioreg -rd1 -c IOPlatformExpertDevice"] = IOREG
    getattr(bakebook, step)("macos")
    files = [Path(c[c.index("--file") + 1]).name for c in _bundles(fake_ctx)]
    work = ["Brewfile.work"] if serial == "SERIAL0001" else []
    assert files == ["Brewfile", "Brewfile", *work]


def _bundle_envs(fake_ctx: FakeCtx) -> list[dict[str, str]]:
    return [
        env
        for cmd, env in zip(fake_ctx.commands, fake_ctx.envs, strict=True)
        if cmd[:2] == ["brew", "bundle"]
    ]


@pytest.mark.parametrize("step", ["_setup_platform_tools", "_update_platform_tools"])
def test_sudo_asks_in_a_dialog_because_bake_detaches_the_terminal(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    brewfiles: Path,
    step: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SUDO_ASKPASS", raising=False)
    getattr(bakebook, step)("macos")
    askpass = brewfiles / "src" / "lib" / "sudo-askpass"
    assert {e["SUDO_ASKPASS"] for e in _bundle_envs(fake_ctx)} == {str(askpass)}


def test_an_askpass_the_owner_set_is_kept(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    brewfiles: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del brewfiles
    monkeypatch.setenv("SUDO_ASKPASS", "/usr/local/bin/my-askpass")
    bakebook._setup_platform_tools("macos")
    assert all("SUDO_ASKPASS" not in e for e in _bundle_envs(fake_ctx))


@pytest.mark.parametrize(
    ("own", "opts"),
    [
        (None, "--adopt"),
        ("--no-quarantine", "--no-quarantine --adopt"),
        ("--adopt", "--adopt"),
    ],
)
def test_an_app_already_installed_is_adopted_not_a_failure(
    bakebook: bakefile.MyBakebook,
    fake_ctx: FakeCtx,
    brewfiles: Path,
    monkeypatch: pytest.MonkeyPatch,
    own: str | None,
    opts: str,
) -> None:
    del brewfiles
    if own is None:
        monkeypatch.delenv("HOMEBREW_CASK_OPTS", raising=False)
    else:
        monkeypatch.setenv("HOMEBREW_CASK_OPTS", own)
    bakebook._setup_platform_tools("macos")
    assert {e["HOMEBREW_CASK_OPTS"] for e in _bundle_envs(fake_ctx)} == {opts}


def test_a_failed_brewfile_does_not_stop_the_next_and_setup_still_fails(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path
) -> None:
    private = brewfiles / "private" / "src" / "lib" / "Brewfile"
    (private.parent / "machines.toml").write_text(
        '"SERIAL0001" = { name = "work-mac", roles = ["work"] }\n'
    )
    (private.parent / "Brewfile.work").write_text('cask "zoom"\n')
    fake_ctx.stdout["ioreg -rd1 -c IOPlatformExpertDevice"] = IOREG
    fake_ctx.failing.add(f"brew bundle install --file {private}")
    with pytest.raises(SystemExit, match=r"private/src/lib/Brewfile\b"):
        bakebook._setup_platform_tools("macos")
    assert [Path(c[-1]).name for c in _bundles(fake_ctx)][-1] == "Brewfile.work"


def test_the_askpass_helper_is_an_executable_script() -> None:
    from src.python.core import repo

    helper = repo.ROOT / "src" / "lib" / "sudo-askpass"
    assert helper.is_file()
    assert helper.stat().st_mode & 0o111


def _removals(fake_ctx: FakeCtx) -> list[list[str]]:
    return [
        c
        for c in fake_ctx.commands
        if c[:2] in (["mise", "prune"], ["brew", "cleanup"])
        or c[:3] == ["uv", "cache", "prune"]
    ]


def test_update_prunes_old_tool_versions_and_uv_cache_after_upgrading(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx
) -> None:
    bakebook._update_tools()
    commands = [" ".join(c) for c in fake_ctx.commands]
    assert commands[-2:] == ["mise prune --yes", "uv cache prune"]
    assert commands.index("mise upgrade") < commands.index("mise prune --yes")


def test_update_cleans_up_homebrew_after_the_brewfile_upgrades_on_macos(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path
) -> None:
    del brewfiles
    bakebook._update_platform_tools("macos")
    brew = [c for c in fake_ctx.commands if c[0] == "brew"]
    assert [c[:3] for c in brew] == [
        ["brew", "bundle", "upgrade"],
        ["brew", "bundle", "upgrade"],
        ["brew", "cleanup"],
    ]


def test_update_runs_no_homebrew_cleanup_off_macos(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path
) -> None:
    del brewfiles
    bakebook._update_platform_tools("linux")
    assert _removals(fake_ctx) == []


def test_setup_removes_nothing(
    bakebook: bakefile.MyBakebook, fake_ctx: FakeCtx, brewfiles: Path
) -> None:
    del brewfiles
    bakebook._setup_platform_tools("macos")
    bakebook._setup_tools()
    assert fake_ctx.commands
    assert _removals(fake_ctx) == []
