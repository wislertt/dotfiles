from pathlib import Path

import pytest

from src.python.dedupe import (
    Duplicate,
    brew_casks,
    brew_formulae,
    cargo_global,
    declared_casks,
    declared_mise_tools,
    dedupe,
    go_global,
    npm_global,
    pipx_global,
)
from tests.unit.conftest import FakeCtx


class FakeManager:
    """A package manager with a fixed install list that records what it is asked to remove."""

    def __init__(self, name: str, installed: set[str], refuses: set[str] | None = None):
        self.name = name
        self.binary = name
        self._installed = set(installed)
        self._refuses = refuses or set()
        self.removed: list[str] = []

    def installed(self) -> set[str]:
        return set(self._installed)

    def uninstall(self, name: str) -> bool:
        if name in self._refuses:
            return False
        self._installed.discard(name)
        self.removed.append(name)
        return True


def _replaced(*names: str):
    return lambda name: name in names


def test_dry_run_lists_a_duplicate_and_removes_nothing() -> None:
    brew = FakeManager("brew", {"jq"})
    report = dedupe([brew], declared={"jq"}, replaced=_replaced("jq"), yes=False)
    assert report.duplicates == [Duplicate("brew", "jq")]
    assert brew.removed == []


def test_declared_but_not_yet_installed_is_not_listed() -> None:
    brew = FakeManager("brew", {"jq"})
    report = dedupe([brew], declared={"jq"}, replaced=_replaced(), yes=True)
    assert report.duplicates == []
    assert brew.removed == []


def test_yes_removes_each_duplicate_and_a_second_pass_finds_none() -> None:
    brew = FakeManager("brew", {"jq", "ripgrep"})
    npm = FakeManager("npm", {"oxfmt"})
    declared = {"jq", "oxfmt"}
    replaced = _replaced("jq", "oxfmt")
    first = dedupe([brew, npm], declared, replaced, yes=True)
    assert first.removed == [Duplicate("brew", "jq"), Duplicate("npm", "oxfmt")]
    assert brew.removed == ["jq"]
    assert dedupe([brew, npm], declared, replaced, yes=False).duplicates == []


def test_a_copy_the_manager_refuses_is_skipped_and_the_rest_still_go() -> None:
    brew = FakeManager("brew", {"jq", "yq"}, refuses={"jq"})
    report = dedupe(
        [brew], declared={"jq", "yq"}, replaced=_replaced("jq", "yq"), yes=True
    )
    assert report.skipped == [Duplicate("brew", "jq")]
    assert report.removed == [Duplicate("brew", "yq")]


def test_a_mapped_name_matches_the_declared_tool() -> None:
    brew = FakeManager("brew", {"python@3.13"})
    report = dedupe(
        [brew],
        declared={"python"},
        replaced=_replaced("python"),
        yes=True,
        aliases={"python@3.13": "python"},
    )
    assert report.removed == [Duplicate("brew", "python@3.13")]


NPM_LS = """{
  "name": "lib",
  "dependencies": {
    "ctx7": {"version": "0.4.0", "overridden": false},
    "oxfmt": {"version": "0.9.0", "overridden": false}
  }
}"""
CARGO_LIST = """typos-cli v1.37.0:
    typos
zerv v0.8.6:
    zerv
"""


@pytest.mark.parametrize(
    ("make", "list_cmd", "output", "names", "remove_cmd"),
    [
        (
            brew_formulae,
            "brew leaves",
            "act\nbat\n",
            {"act", "bat"},
            ["brew", "uninstall", "--formula", "act"],
        ),
        (
            brew_casks,
            "brew list --cask -1",
            "zed\ndocker-desktop\n",
            {"zed", "docker-desktop"},
            ["brew", "uninstall", "--cask", "zed"],
        ),
        (
            npm_global,
            "npm ls -g --depth=0 --json",
            NPM_LS,
            {"ctx7", "oxfmt"},
            ["npm", "uninstall", "-g", "ctx7"],
        ),
        (
            pipx_global,
            "pipx list --short",
            "poetry 2.4.1\npoetry 2.4.0\n",
            {"poetry"},
            ["pipx", "uninstall", "poetry"],
        ),
        (
            cargo_global,
            "cargo install --list",
            CARGO_LIST,
            {"typos-cli", "zerv"},
            ["cargo", "uninstall", "typos-cli"],
        ),
    ],
)
def test_adapter_lists_names_and_removes_through_its_own_manager(
    make, list_cmd, output, names, remove_cmd
) -> None:
    ctx = FakeCtx(stdout={list_cmd: output})
    manager = make(ctx)
    assert manager.installed() == names
    assert manager.uninstall(remove_cmd[-1]) is True
    assert ctx.commands[-1] == remove_cmd


def test_adapter_reports_a_refused_removal() -> None:
    ctx = FakeCtx(returncode=1)
    assert brew_formulae(ctx).uninstall("jq") is False


def _go_bin(tmp_path: Path, gobin: str = "") -> tuple[FakeCtx, Path]:
    bin_dir = tmp_path / "go" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "gopls").write_text("")
    (bin_dir / "dlv").write_text("")
    out = f"{gobin}\n{tmp_path / 'go'}\n"
    return FakeCtx(stdout={"go env GOBIN GOPATH": out}), bin_dir


def test_go_adapter_lists_and_removes_binaries_in_gopath_bin(tmp_path: Path) -> None:
    ctx, bin_dir = _go_bin(tmp_path)
    manager = go_global(ctx)
    assert manager.installed() == {"gopls", "dlv"}
    assert manager.uninstall("gopls") is True
    assert not (bin_dir / "gopls").exists()
    assert manager.uninstall("gopls") is False


def test_go_adapter_prefers_gobin(tmp_path: Path) -> None:
    other = tmp_path / "elsewhere"
    other.mkdir()
    (other / "staticcheck").write_text("")
    ctx, _ = _go_bin(tmp_path, gobin=str(other))
    assert go_global(ctx).installed() == {"staticcheck"}


def test_declared_mise_tools_drop_the_backend_prefix(tmp_path: Path) -> None:
    (tmp_path / "mise.toml").write_text(
        '[tools]\njq = "latest"\n"npm:oxfmt" = "latest"\n'
        '"pipx:bakefile" = { version = "latest", extras = "locked" }\n'
        '"go:golang.org/x/tools/gopls" = "latest"\n'
    )
    (tmp_path / "mise.private.toml").write_text('[tools]\n"cargo:zerv" = "latest"\n')
    assert declared_mise_tools(tmp_path) == {
        "jq": "jq",
        "oxfmt": "npm:oxfmt",
        "bakefile": "pipx:bakefile",
        "gopls": "go:golang.org/x/tools/gopls",
        "zerv": "cargo:zerv",
    }


def test_declared_mise_tools_without_a_tools_table_or_private_file(
    tmp_path: Path,
) -> None:
    (tmp_path / "mise.toml").write_text("[bootstrap]\ndotfile_groups = []\n")
    assert declared_mise_tools(tmp_path) == {}


def test_declared_casks_come_from_every_brewfile(tmp_path: Path) -> None:
    public = tmp_path / "Brewfile"
    public.write_text('# apps\ncask "zed"\ncask "docker-desktop", args: { x: 1 }\n')
    private = tmp_path / "Brewfile.private"
    private.write_text('cask "kiro"\n')
    assert declared_casks([public, private]) == {"zed", "docker-desktop", "kiro"}


def test_declared_scoped_npm_package_keeps_its_scope(tmp_path: Path) -> None:
    (tmp_path / "mise.toml").write_text('[tools]\n"npm:@scope/pkg" = "latest"\n')
    assert declared_mise_tools(tmp_path) == {"@scope/pkg": "npm:@scope/pkg"}


def test_a_versioned_formula_matches_the_declared_tool() -> None:
    brew = FakeManager("brew", {"python@3.14"})
    report = dedupe(
        [brew], declared={"python"}, replaced=_replaced("python"), yes=False
    )
    assert report.duplicates == [Duplicate("brew", "python@3.14")]


def test_go_adapter_never_removes_a_symlink(tmp_path: Path) -> None:
    ctx, bin_dir = _go_bin(tmp_path)
    (bin_dir / "linked").symlink_to(bin_dir / "gopls")
    manager = go_global(ctx)
    assert "linked" not in manager.installed()
    assert manager.uninstall("linked") is False
    assert (bin_dir / "linked").is_symlink()


def test_go_adapter_uses_the_first_gopath_entry(tmp_path: Path) -> None:
    ctx, _ = _go_bin(tmp_path)
    ctx.stdout["go env GOBIN GOPATH"] = f"\n{tmp_path / 'go'}:/somewhere/else\n"
    assert go_global(ctx).installed() == {"gopls", "dlv"}
