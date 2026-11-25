import json
import re
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

import pytest

from src.python import bakefile
from src.python.commands import tidy
from src.python.core import tidy as tidy_core
from tests.unit.conftest import FakeCtx


class Machine:
    """A temp home, PATH and set of installed managers standing in for the real machine."""

    def __init__(
        self, root: Path, home: Path, ctx: FakeCtx, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self.root = root
        self.home = home
        self.ctx = ctx
        self.monkeypatch = monkeypatch
        self.managers: set[str] = set()
        self.path: list[Path] = []
        self.applications = home / "Applications-root"
        self.applications.mkdir()
        monkeypatch.setattr(tidy, "APPLICATIONS", self.applications)
        monkeypatch.setattr(tidy, "IS_MACOS", False)
        self.system_go = home / "usr-local-go"
        monkeypatch.setattr(tidy_core, "SYSTEM_LEFTOVERS", (self.system_go,))
        monkeypatch.setattr(
            tidy.shutil,
            "which",
            lambda name: f"/fake/{name}" if name in self.managers else None,
        )
        monkeypatch.setattr(tidy, "SYSTEM_BIN_DIRS", (str(home / "usr-bin"),))
        self.set_path()

    def set_path(self, *dirs: Path) -> None:
        self.path = list(dirs)
        self.monkeypatch.setenv("PATH", ":".join(str(d) for d in dirs))

    def output(self, cmd: str, stdout: str) -> None:
        self.managers.add(cmd.split()[0])
        self.ctx.stdout[cmd] = stdout

    def brewfile(
        self,
        text: str,
        private: bool = False,
        casks: str = "",
        formulae: str = "",
        name: str = "Brewfile",
    ) -> None:
        """A Brewfile and what Homebrew's cleanup listing (exit 1 when non-empty) says against it."""
        base = self.root / "private" if private or name != "Brewfile" else self.root
        path = base / "src" / "lib" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        listing = "".join(
            f"Would uninstall {heading}:\n" + "".join(f"{n}\n" for n in names.split())
            for heading, names in (("casks", casks), ("formulae", formulae))
            if names
        )
        cmd = f"brew bundle cleanup --file {path}"
        self.output(cmd, listing + "Would untap:\nsome/tap\n")
        self.ctx.failing.add(cmd)

    def keep(self, text: str, private: bool = False, name: str = "keep.toml") -> None:
        base = self.root / "private" if private or name != "keep.toml" else self.root
        path = base / "src" / "lib" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def is_listed_as(self, role: str) -> None:
        """This machine's serial, mapped to the role in the private machine list."""
        path = self.root / "private" / "src" / "lib" / "machines.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'"SERIAL0001" = {{ name = "work-mac", roles = ["{role}"] }}\n')
        self.output(
            "ioreg -rd1 -c IOPlatformExpertDevice",
            '    "IOPlatformSerialNumber" = "SERIAL0001"\n',
        )

    def ran(self) -> list[list[str]]:
        return self.ctx.commands


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
) -> Machine:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return Machine(fake_repo, home, fake_ctx, monkeypatch)


Run = Callable[..., tuple[list[str], int]]


@pytest.fixture
def run(bakebook: bakefile.MyBakebook, machine: Machine) -> Run:
    """Runs tidy; returns the listed lines and the exit code."""
    del machine  # set up first

    def _run(check: bool = False, **options: bool) -> tuple[list[str], int]:
        with patch.object(tidy, "console") as console:
            code = 0
            try:
                bakebook.tidy(check=check, **options)
            except SystemExit as exit_:
                if isinstance(exit_.code, str):
                    raise
                code = int(exit_.code or 0)
        # status lines carry their level, as the console's icon would show it
        marks = {
            "echo": "",
            "success": "ok: ",
            "info": "info: ",
            "warning": "warn: ",
            "error": "error: ",
        }
        return [f"{marks[c[0]]}{c.args[0]}" for c in console.method_calls], code

    return _run


def _strays(lines: list[str]) -> list[list[str]]:
    """The indented lines of the check report, split into the key and any command."""
    return [
        re.split(r"\s{2,}", line.strip()) for line in lines if line.startswith("  ")
    ]


def _listed(lines: list[str]) -> list[str]:
    return [stray[0] for stray in _strays(lines)]


def _by_hand(lines: list[str]) -> dict[str, str]:
    """The command named for each Stray Tidy only names."""
    return {key: cmd for key, *rest in _strays(lines) for cmd in rest}


def test_a_clean_machine_passes_the_check(machine: Machine, run: Run) -> None:
    del machine
    lines, code = run(check=True)
    assert (lines, code) == ([], 0)


def test_a_homebrew_leaf_not_in_a_brewfile_is_a_stray(
    machine: Machine, run: Run
) -> None:
    # libidn2 is a dependency of wget, so not a leaf
    machine.brewfile('brew "mise"\n', formulae="libidn2 wget")
    machine.output("brew leaves", "mise\nwget\n")
    lines, code = run(check=True)
    assert _listed(lines) == ["brew:wget"]
    assert code == 1
    assert not [c for c in machine.ran() if "uninstall" in c]


@pytest.fixture
def brew(machine: Machine) -> Machine:
    machine.brewfile('brew "mise"\ncask "zed"\n', casks="firefox", formulae="wget")
    machine.output("brew leaves", "mise\nwget\n")
    return machine


def test_casks_not_in_a_brewfile_are_strays(brew: Machine, run: Run) -> None:
    lines, _ = run(check=True)
    assert _listed(lines) == ["brew:wget", "cask:firefox"]


def test_a_cask_in_the_private_brewfile_is_declared(brew: Machine, run: Run) -> None:
    brew.brewfile('cask "firefox"\n', private=True, casks="zed", formulae="wget")
    lines, _ = run(check=True)
    assert _listed(lines) == ["brew:wget"]


def test_a_cask_in_this_machines_role_brewfile_is_declared(
    brew: Machine, run: Run
) -> None:
    brew.brewfile(
        'cask "firefox"\n', name="Brewfile.work", casks="zed", formulae="wget"
    )
    brew.is_listed_as("work")
    lines, _ = run(check=True)
    assert _listed(lines) == ["brew:wget"]


def test_a_role_brewfile_counts_for_nothing_on_another_machine(
    brew: Machine, run: Run
) -> None:
    brew.brewfile(
        'cask "firefox"\n', name="Brewfile.work", casks="zed", formulae="wget"
    )
    brew.is_listed_as("studio")
    lines, _ = run(check=True)
    assert _listed(lines) == ["brew:wget", "cask:firefox"]


def test_a_formula_a_declared_app_needs_is_not_a_stray(
    machine: Machine, run: Run
) -> None:
    # Homebrew's cleanup listing keeps a declared cask's formula dependencies
    machine.brewfile('cask "zed"\n', formulae="wget")
    machine.output("brew leaves", "wget\ngit-lfs\n")
    lines, _ = run(check=True)
    assert _listed(lines) == ["brew:wget"]


def test_tidy_removes_every_stray_without_asking_then_autoremoves(
    brew: Machine, run: Run
) -> None:
    lines, code = run()
    assert code == 0
    assert lines[-1] == "Removed 2. Nothing needs you"
    assert brew.ran()[-3:] == [
        ["brew", "uninstall", "wget"],
        ["brew", "uninstall", "--cask", "firefox"],
        ["brew", "autoremove"],
    ]


def test_no_autoremove_when_nothing_was_uninstalled(brew: Machine, run: Run) -> None:
    brew.keep('"brew:wget" = "x"\n"cask:firefox" = "x"\n')
    run()
    assert ["brew", "autoremove"] not in brew.ran()


@pytest.fixture
def managers(machine: Machine) -> Machine:
    machine.output(
        "uv tool list", "ruff v0.6.0\n- ruff\nspecify-cli v0.0.1\n- specify\n"
    )
    machine.output("cargo install --list", "typos-cli v1.37.0:\n    typos\n")
    machine.output(
        "npm ls -g --depth=0 --json",
        '{"dependencies": {"npm": {}, "corepack": {}, "typescript": {}}}',
    )
    machine.output("pnpm ls -g --json", '[{"dependencies": {"tsx": {}}}]')
    return machine


def test_tools_installed_outside_mise_are_strays(managers: Machine, run: Run) -> None:
    lines, _ = run(check=True)
    assert _listed(lines) == [
        "uv:ruff",
        "uv:specify-cli",
        "cargo:typos-cli",
        "npm:typescript",
        "pnpm:tsx",
    ]


def test_each_is_removed_with_the_manager_that_owns_it(
    managers: Machine, run: Run
) -> None:
    run()
    assert managers.ran()[-5:] == [
        ["uv", "tool", "uninstall", "ruff"],
        ["uv", "tool", "uninstall", "specify-cli"],
        ["cargo", "uninstall", "typos-cli"],
        ["npm", "uninstall", "-g", "typescript"],
        ["pnpm", "remove", "-g", "tsx"],
    ]


def test_a_failed_removal_is_reported_the_rest_still_go_and_tidy_fails(
    managers: Machine, run: Run
) -> None:
    managers.ctx.failing.add("cargo uninstall typos-cli")
    _, code = run()
    assert code == 1
    assert ["pnpm", "remove", "-g", "tsx"] in managers.ran()


def test_a_manager_that_fails_or_is_missing_reports_nothing(
    machine: Machine, run: Run
) -> None:
    machine.output("pnpm ls -g --json", "")
    machine.ctx.failing.add("pnpm ls -g --json")
    machine.output("uv tool list", "No tools installed\n")
    lines, code = run(check=True)
    assert (lines, code) == ([], 0)


def test_a_dead_link_in_a_path_directory_is_removed(machine: Machine, run: Run) -> None:
    bin_dir = machine.home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "specify").symlink_to(machine.home / "gone")
    (bin_dir / "live").symlink_to(_exe(machine.home / "tools", "live") / "live")
    machine.set_path(bin_dir)
    lines, _ = run(check=True)
    assert _listed(lines) == ["dead-link:~/.local/bin/specify"]
    run()
    assert machine.ran()[-1] == ["rm", str(bin_dir / "specify")]


def test_a_dead_link_in_a_directory_needing_an_administrator_is_only_named(
    machine: Machine, run: Run
) -> None:
    system = machine.home / "system-bin"
    system.mkdir()
    (system / "old").symlink_to(machine.home / "gone")
    system.chmod(0o555)
    machine.set_path(system)
    try:
        lines, _ = run(check=True)
        run()
    finally:
        system.chmod(0o755)
    assert _by_hand(lines) == {
        "dead-link:~/system-bin/old": f"sudo rm {system / 'old'}"
    }
    assert not [c for c in machine.ran() if c[0] == "rm"]


def test_a_leftover_folder_in_home_is_made_writable_then_removed(
    machine: Machine, run: Run
) -> None:
    (machine.home / ".pyenv" / "versions").mkdir(parents=True)
    lines, _ = run(check=True)
    assert _listed(lines) == ["leftover:~/.pyenv"]
    run()
    assert machine.ran()[-2:] == [
        ["chmod", "-R", "u+w", str(machine.home / ".pyenv")],
        ["rm", "-rf", str(machine.home / ".pyenv")],
    ]


def test_a_leftover_folder_outside_home_is_only_named(
    machine: Machine, run: Run
) -> None:
    machine.system_go.mkdir()
    lines, _ = run(check=True)
    run()
    assert _by_hand(lines) == {
        f"leftover:{machine.system_go}": f"sudo rm -rf {machine.system_go}"
    }
    assert machine.ran() == []


def test_an_unknown_file_in_the_local_bin_is_only_named(
    machine: Machine, run: Run
) -> None:
    bin_dir = _exe(machine.home / ".local" / "bin", "zcode")
    (bin_dir / "linked").symlink_to(bin_dir / "zcode")
    lines, _ = run(check=True)
    run()
    assert _by_hand(lines) == {"local-bin:zcode": f"rm {bin_dir / 'zcode'}"}
    assert machine.ran() == []


@pytest.fixture
def mac(machine: Machine) -> Machine:
    machine.monkeypatch.setattr(tidy, "IS_MACOS", True)
    for app in ("Zed.app", "Firefox.app", "Notion.app", "Utilities"):
        (machine.applications / app).mkdir()
    machine.brewfile('cask "zed"\n', casks="firefox")
    machine.output(
        "brew info --cask --installed --json=v2",
        '{"casks": [{"token": "zed", "artifacts": [{"app": ["Zed.app"]}]},'
        ' {"token": "firefox", "artifacts": [{"uninstall": []},'
        ' {"app": ["Firefox.app"], "target": "'
        + str(machine.applications / "Firefox.app")
        + '"}]}]}',
    )
    return machine


def test_an_app_no_cask_installed_is_only_named(mac: Machine, run: Run) -> None:
    lines, _ = run(check=True)
    assert _listed(lines) == ["cask:firefox", "app:Notion"]
    run()
    assert _by_hand(lines) == {
        "app:Notion": f"rm -rf {mac.applications / 'Notion.app'}"
    }
    assert not [c for c in mac.ran() if c[0] == "rm"]


def _pkg_cask(mac: Machine, uninstall: dict[str, object]) -> None:
    mac.output(
        "brew info --cask --installed --json=v2",
        json.dumps(
            {"casks": [{"token": "vendor", "artifacts": [{"uninstall": [uninstall]}]}]}
        ),
    )


def test_an_app_a_cask_installs_from_a_pkg_is_owned_by_the_receipt(
    mac: Machine, run: Run
) -> None:
    for app in ("Docs.app", "Drive.app"):
        (mac.applications / app).mkdir()
    _pkg_cask(mac, {"pkgutil": ["com\\.vendor\\..*"]})
    mac.output(
        "pkgutil --pkgs=com\\.vendor\\..*", "com.vendor.drive\ncom.vendor.docs\n"
    )
    mac.output("pkgutil --files com.vendor.drive", "Drive.app\nDrive.app/Contents\n")
    # a receipt may record the app under another location, as an updater's clone does
    mac.output(
        "pkgutil --files com.vendor.docs", "Docs.app\nDocs.app/Contents/Docs.app\n"
    )
    lines, _ = run(check=True)
    assert [s for s in _listed(lines) if s.startswith("app:")] == [
        "app:Firefox",
        "app:Notion",
        "app:Zed",
    ]


def test_an_app_a_cask_deletes_on_uninstall_is_owned(mac: Machine, run: Run) -> None:
    _pkg_cask(
        mac,
        {
            "pkgutil": "com.vendor",
            "delete": [str(mac.applications / "Notion.app"), "/Library/x"],
        },
    )
    lines, _ = run(check=True)
    assert "app:Notion" not in _listed(lines)
    assert "app:Zed" in _listed(lines)


def test_apps_are_not_looked_at_off_macos(mac: Machine, run: Run) -> None:
    mac.monkeypatch.setattr(tidy, "IS_MACOS", False)
    lines, _ = run(check=True)
    assert "app:Notion" not in _listed(lines)


@pytest.fixture
def jq(machine: Machine, tmp_path: Path) -> dict[str, Path]:
    """jq declared in mise and installed, with a Homebrew copy on PATH."""
    (machine.root / "mise.toml").write_text('[tools]\njq = "latest"\n')
    dirs = {
        "mise": _exe(tmp_path / "mise" / "installs" / "jq", "jq"),
        "brew": _exe(tmp_path / "brew", "jq"),
    }
    machine.output("mise bin-paths jq", f"{dirs['mise']}\n")
    machine.set_path(dirs["mise"], dirs["brew"], dirs["brew"])
    return dirs


def test_a_copy_of_a_declared_mise_tool_is_a_stray_reported_once(
    machine: Machine, jq: dict[str, Path], run: Run
) -> None:
    lines, _ = run(check=True)
    run()
    assert _listed(lines) == [f"duplicate:{jq['brew'] / 'jq'}"]
    assert {c[0] for c in machine.ran()} == {"mise"}  # only `mise bin-paths`


@pytest.mark.parametrize(
    "place",
    ["mise/shims", "project/.venv/bin", "usr-bin"],
    ids=["shims", "venv", "system"],
)
def test_shims_project_virtualenvs_and_system_directories_are_not_copies(
    machine: Machine, jq: dict[str, Path], run: Run, place: str
) -> None:
    other = _exe(machine.home / place, "jq")
    machine.set_path(jq["mise"], other)
    lines, _ = run(check=True)
    assert lines == []


def test_a_declared_tool_mise_has_not_installed_is_not_reported(
    machine: Machine, jq: dict[str, Path], run: Run
) -> None:
    del jq
    machine.ctx.failing.add("mise bin-paths jq")
    lines, _ = run(check=True)
    assert lines == []


def test_every_binary_the_tool_ships_is_checked_and_nothing_else(
    machine: Machine, tmp_path: Path, run: Run
) -> None:
    (machine.root / "mise.toml").write_text('[tools]\nuv = "latest"\n')
    own = _exe(_exe(tmp_path / "mise" / "uv", "uv"), "uvx")
    other = _exe(_exe(tmp_path / "brew", "uvx"), "ripgrep")
    (other / "uv").write_text("")  # not executable, so not a copy
    machine.output("mise bin-paths uv", f"{own}\n")
    machine.set_path(own, other)
    lines, _ = run(check=True)
    assert _listed(lines) == [f"duplicate:{other / 'uvx'}"]


def test_a_symlink_to_another_install_is_a_copy(
    machine: Machine, jq: dict[str, Path], tmp_path: Path, run: Run
) -> None:
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "jq").symlink_to(jq["brew"] / "jq")
    machine.set_path(jq["mise"], linked)
    lines, _ = run(check=True)
    assert _listed(lines) == [f"duplicate:{linked / 'jq'}"]


@pytest.mark.parametrize(
    "config",
    [
        "mise.toml",
        "mise.private.toml",
        "src/config/mise/config.toml",
        "private/src/config/mise/config.toml",
    ],
)
def test_tools_declared_in_any_mise_config_are_checked(
    machine: Machine, run: Run, config: str
) -> None:
    path = machine.root / config
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[tools]\n"npm:oxfmt" = "latest"\n')
    machine.output("mise bin-paths npm:oxfmt", "")
    run(check=True)
    assert ["mise", "bin-paths", "npm:oxfmt"] in machine.ran()


def test_strays_on_the_public_and_private_keep_lists_are_skipped(
    managers: Machine, run: Run
) -> None:
    managers.keep('"uv:ruff" = "pinned for an old project"\n')
    managers.keep(
        '"cargo:typos-cli" = "work linter"\n"pnpm:tsx" = "work scripts"\n',
        private=True,
    )
    lines, _ = run(check=True)
    assert _listed(lines) == ["uv:specify-cli", "npm:typescript"]
    run()
    assert not [c for c in managers.ran() if "ruff" in c or "tsx" in c]


@pytest.mark.parametrize(
    ("role", "listed"), [("work", []), ("studio", ["cargo:typos-cli"])]
)
def test_a_role_keep_list_applies_only_on_a_machine_with_that_role(
    machine: Machine, run: Run, role: str, listed: list[str]
) -> None:
    machine.output("cargo install --list", "typos-cli v1.37.0:\n    typos\n")
    machine.keep('"cargo:typos-cli" = "work linter"\n', name="keep.work.toml")
    machine.is_listed_as(role)
    lines, _ = run(check=True)
    assert _listed(lines) == listed


def test_the_check_passes_when_every_stray_is_kept(machine: Machine, run: Run) -> None:
    machine.output("cargo install --list", "typos-cli v1.37.0:\n    typos\n")
    machine.keep('"cargo:typos-cli" = "pre-commit hook"\n')
    assert run(check=True) == ([], 0)


@pytest.mark.parametrize(
    "entry",
    ['"cargo:typos-cli" = ""\n', '"typos-cli" = "no kind"\n', '"cargo:x" = 1\n'],
    ids=["no-reason", "no-kind", "not-text"],
)
def test_a_keep_entry_without_a_kind_or_reason_fails_clearly(
    machine: Machine, run: Run, entry: str
) -> None:
    machine.keep(entry)
    with pytest.raises(SystemExit, match="keep.toml"):
        run(check=True)


def test_a_dead_link_in_a_system_directory_is_not_reported(
    machine: Machine, run: Run
) -> None:
    system = machine.home / "usr-bin"
    system.mkdir()
    (system / "weakpass_edit").symlink_to(machine.home / "gone")
    machine.set_path(system)
    assert run(check=True) == ([], 0)


def _gpg_key(
    id_: int, name: str, key_id: str, expires: str | None
) -> dict[str, object]:
    return {"id": id_, "name": name, "key_id": key_id, "expires_at": expires}


@pytest.fixture
def github(machine: Machine) -> Machine:
    """This machine's signing key and three others on GitHub."""
    machine.output("git config --get user.signingkey", "<a@b.c>\n")
    machine.output(
        "gpg --list-secret-keys --with-colons <a@b.c>",
        "sec:u:255:22:AAAA:1:::u:::scSC:::+::ed25519:::0:\nfpr:::::::::FPR-AAAA:\n",
    )
    keys = [
        _gpg_key(1, "dotfiles: this-mac (aaaaaa)", "AAAA", "2000-01-01T00:00:00+00:00"),
        _gpg_key(2, "dotfiles: old-mac (bbbbbb)", "BBBB", "2000-01-01T00:00:00+00:00"),
        _gpg_key(3, "dotfiles: linux (cccccc)", "CCCC", "2999-01-01T00:00:00+00:00"),
        _gpg_key(4, "old-laptop", "DDDD", None),
    ]
    machine.output("gh api --paginate --slurp user/gpg_keys", json.dumps([keys]))
    return machine


def test_an_expired_signing_key_is_a_stray_and_this_machines_key_is_not(
    github: Machine, run: Run
) -> None:
    lines, _ = run(check=True)
    assert _listed(lines) == [
        "signing-key:dotfiles: old-mac (bbbbbb)",
        "signing-key:old-laptop",
    ]


def test_an_expired_signing_key_is_deleted_with_the_stored_gh_login(
    github: Machine, run: Run
) -> None:
    run()
    deletes = [c for c in github.ran() if "DELETE" in c]
    assert deletes == [
        ["env", "-u", "GITHUB_TOKEN", "-u", "GH_TOKEN"]
        + ["gh", "api", "-X", "DELETE", "user/gpg_keys/2"]
    ]


def test_a_signing_key_that_never_expires_is_only_named(
    github: Machine, run: Run
) -> None:
    lines, _ = run(check=True)
    assert _by_hand(lines) == {
        "signing-key:old-laptop": "gh api -X DELETE user/gpg_keys/4"
    }


KEEP_HINT = '"kind:name" = "reason" in src/lib/keep.toml'


def test_the_check_shows_what_tidy_removes_then_what_needs_you_by_kind(
    managers: Machine, run: Run
) -> None:
    managers.system_go.mkdir()
    lines, code = run(check=True)
    assert code == 1
    assert lines == [
        "Removed by `bake tidy` (5)",
        "  uv:ruff",
        "  uv:specify-cli",
        "  cargo:typos-cli",
        "  npm:typescript",
        "  pnpm:tsx",
        "",
        f"Needs you (1): run the command, or keep it with {KEEP_HINT}",
        "",
        "leftover (1): outside home, so it needs sudo",
        f"  leftover:{managers.system_go}  sudo rm -rf {managers.system_go}",
    ]


def test_tidy_says_what_it_checked_removed_and_left(
    managers: Machine, run: Run
) -> None:
    managers.system_go.mkdir()
    managers.ctx.failing.add("cargo uninstall typos-cli")
    lines, _ = run()
    assert lines == [
        "info: Homebrew: skipped, brew is not installed",
        "ok: Removed uv:ruff",
        "ok: Removed uv:specify-cli",
        "ok: uv tools: clean",
        "warn: Could not remove cargo:typos-cli",
        "info: cargo crates: 1 need you",
        "ok: Removed npm:typescript",
        "ok: npm globals: clean",
        "ok: Removed pnpm:tsx",
        "ok: pnpm globals: clean",
        "ok: PATH: clean",
        "info: Old tool-manager folders: 1 need you",
        "ok: ~/.local/bin: clean",
        "info: Copies of mise tools: skipped, mise is not installed",
        "info: GitHub signing keys: skipped, gh is not installed",
        "info: GitHub SSH keys: skipped, gh is not installed",
        "Removed 4. 1 could not be removed. 2 need you: run `bake tidy --check`",
    ]


DOCKER_PRUNE = ["docker", "system", "prune", "--all", "--force"]


def test_caches_are_left_alone_without_the_flag(machine: Machine, run: Run) -> None:
    machine.output("docker info", "")
    machine.managers.add("mo")
    run()
    assert DOCKER_PRUNE not in machine.ran()
    assert ["mo", "clean"] not in machine.ran()


def test_caches_clears_docker_without_volumes_and_mole_on_macos(
    machine: Machine, run: Run
) -> None:
    machine.monkeypatch.setattr(tidy, "IS_MACOS", True)
    machine.output("docker info", "")
    machine.managers.add("mo")
    lines, code = run(caches=True)
    assert code == 0
    assert DOCKER_PRUNE in machine.ran()
    assert ["mo", "clean"] in machine.ran()
    assert "ok: Docker: caches cleared" in lines
    assert "ok: Mole: caches cleared" in lines


def test_volumes_adds_unused_docker_volumes(machine: Machine, run: Run) -> None:
    machine.output("docker info", "")
    run(caches=True, volumes=True)
    assert [*DOCKER_PRUNE, "--volumes"] in machine.ran()


def test_volumes_without_caches_fails_and_removes_nothing(
    machine: Machine, run: Run
) -> None:
    machine.output("docker info", "")
    lines, code = run(volumes=True)
    assert code == 1
    assert lines == ["error: --volumes needs --caches"]
    assert machine.ran() == []


def test_caches_skips_docker_when_it_is_not_running_and_mole_off_macos(
    machine: Machine, run: Run
) -> None:
    machine.output("docker info", "")
    machine.ctx.failing.add("docker info")
    machine.managers.add("mo")
    lines, code = run(caches=True)
    assert code == 0
    assert "info: Docker: skipped, Docker is not running" in lines
    assert DOCKER_PRUNE not in machine.ran()
    assert ["mo", "clean"] not in machine.ran()


def test_a_failed_cache_clear_fails_tidy(machine: Machine, run: Run) -> None:
    machine.output("docker info", "")
    machine.ctx.failing.add(" ".join(DOCKER_PRUNE))
    lines, code = run(caches=True)
    assert code == 1
    assert "warn: Docker: could not clear caches" in lines


def test_the_check_ignores_caches(machine: Machine, run: Run) -> None:
    machine.output("docker info", "")
    _, code = run(check=True, caches=True)
    assert code == 0
    assert DOCKER_PRUNE not in machine.ran()


HOST = "aarch64-apple-darwin"


@pytest.fixture
def rust(machine: Machine) -> Machine:
    machine.output(
        "rustup toolchain list",
        f"stable-{HOST} (active, default)\nbeta-{HOST}\nnightly-{HOST}\n"
        f"1.100.0-{HOST}\n1.99.1-{HOST}\n",
    )
    return machine


def test_a_numbered_rust_toolchain_is_a_stray_and_a_channel_is_not(
    rust: Machine, run: Run
) -> None:
    lines, code = run(check=True)
    assert _listed(lines) == [
        f"rust-toolchain:1.100.0-{HOST}",
        f"rust-toolchain:1.99.1-{HOST}",
    ]
    assert code == 1


def _repos(machine: Machine, pins: dict[str, str]) -> None:
    """A repos root named in tidy.toml, with each file under it written as given."""
    root = machine.home / "repos"
    (machine.root / "src" / "lib" / "tidy.toml").write_text(f'repos = ["{root}"]\n')
    for relative, text in pins.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(text)


def test_a_toolchain_a_repo_pins_is_kept(rust: Machine, run: Run) -> None:
    _repos(
        rust,
        {
            "me/app/rust-toolchain.toml": '[toolchain]\nchannel = "1.100"\n',
            "me/unpinned/Cargo.toml": "",
        },
    )
    lines, _ = run(check=True)
    assert _listed(lines) == [f"rust-toolchain:1.99.1-{HOST}"]


def test_the_legacy_pin_file_counts_and_a_minor_pin_keeps_only_its_own_patches(
    rust: Machine, run: Run
) -> None:
    _repos(rust, {"old/rust-toolchain": "1.99\n"})
    lines, _ = run(check=True)
    assert _listed(lines) == [f"rust-toolchain:1.100.0-{HOST}"]


def test_a_pin_below_a_repo_root_is_not_read(rust: Machine, run: Run) -> None:
    _repos(rust, {"me/app/crates/x/rust-toolchain": "1.99.1\n"})
    lines, _ = run(check=True)
    assert len(_listed(lines)) == 2


def test_an_unpinned_toolchain_is_uninstalled_with_rustup_and_a_failure_is_reported(
    rust: Machine, run: Run
) -> None:
    rust.ctx.failing.add(f"rustup toolchain uninstall 1.100.0-{HOST}")
    lines, code = run()
    assert [c for c in rust.ran() if c[:3] == ["rustup", "toolchain", "uninstall"]] == [
        ["rustup", "toolchain", "uninstall", f"1.100.0-{HOST}"],
        ["rustup", "toolchain", "uninstall", f"1.99.1-{HOST}"],
    ]
    assert f"warn: Could not remove rust-toolchain:1.100.0-{HOST}" in lines
    assert f"ok: Removed rust-toolchain:1.99.1-{HOST}" in lines
    assert code == 1


def test_a_kept_toolchain_is_left_alone(rust: Machine, run: Run) -> None:
    rust.keep(f'"rust-toolchain:1.99.1-{HOST}" = "builds an old release"\n')
    lines, _ = run(check=True)
    assert _listed(lines) == [f"rust-toolchain:1.100.0-{HOST}"]


def test_a_dated_nightly_is_kept_only_by_its_exact_pin(
    machine: Machine, run: Run
) -> None:
    machine.output(
        "rustup toolchain list",
        f"nightly-2026-01-01-{HOST}\nnightly-2026-02-01-{HOST}\nmy-local-build\n",
    )
    _repos(
        machine,
        {"x/rust-toolchain.toml": '[toolchain]\nchannel = "nightly-2026-01-01"\n'},
    )
    lines, _ = run(check=True)
    assert _listed(lines) == [f"rust-toolchain:nightly-2026-02-01-{HOST}"]


def test_no_rustup_means_no_toolchain_line(machine: Machine, run: Run) -> None:
    lines, code = run()
    assert not [line for line in lines if "Rust" in line]
    assert code == 0


def test_a_pin_file_that_cannot_be_read_counts_for_nothing(
    rust: Machine, run: Run
) -> None:
    _repos(rust, {"a/rust-toolchain.toml": 'toolchain = "1.99.1"\n'})
    not_text = rust.home / "repos" / "b" / "rust-toolchain"
    not_text.parent.mkdir()
    not_text.write_bytes(b"\xff")
    lines, _ = run(check=True)
    assert len(_listed(lines)) == 2


SSH_KEYS = "gh api --paginate --slurp user/keys"
DELETE_SSH_KEY = "env -u GITHUB_TOKEN -u GH_TOKEN gh ssh-key delete"


@pytest.fixture
def ssh(machine: Machine) -> Machine:
    machine.output("gh api --paginate --slurp user/gpg_keys", "[]")
    keys = [{"id": 7, "title": "old-laptop"}, {"id": 9, "title": "work-mac"}]
    machine.output(SSH_KEYS, json.dumps([keys]))
    return machine


def test_every_github_ssh_key_is_only_named_with_the_command_to_delete_it(
    ssh: Machine, run: Run
) -> None:
    lines, code = run(check=True)
    assert _by_hand(lines) == {
        "ssh-key:old-laptop": f"{DELETE_SSH_KEY} 7 --yes",
        "ssh-key:work-mac": f"{DELETE_SSH_KEY} 9 --yes",
    }
    assert code == 1
    run()
    assert not [c for c in ssh.ran() if "delete" in c]


def test_a_kept_ssh_key_is_not_listed(ssh: Machine, run: Run) -> None:
    ssh.keep('"ssh-key:work-mac" = "deploys over ssh"\n', private=True)
    lines, _ = run(check=True)
    assert _listed(lines) == ["ssh-key:old-laptop"]


def test_ssh_keys_gh_cannot_list_are_reported_not_passed(
    machine: Machine, run: Run
) -> None:
    machine.output("gh api --paginate --slurp user/gpg_keys", "[]")
    machine.output(SSH_KEYS, "")
    machine.ctx.failing.add(SSH_KEYS)
    lines, code = run(check=True)
    assert lines == [
        (
            "warn: GitHub SSH keys: not checked, gh needs the read:public_key scope:"
            " run `gh auth refresh -h github.com -s read:public_key`"
        )
    ]
    assert code == 0
