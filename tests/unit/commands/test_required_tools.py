import pytest

from src.python import bakefile
from src.python.commands import setup_update


def test_bws_is_required_and_installed_by_the_tool_manager(
    bakebook: bakefile.MyBakebook,
) -> None:
    assert "bws" in bakebook._get_required_cli_tools()
    assert "bitwarden-secrets-manager" in bakebook._get_mise_tools()


def test_assert_tools_fails_and_names_a_missing_tool(
    bakebook: bakefile.MyBakebook, monkeypatch: pytest.MonkeyPatch
) -> None:
    present = {"bake": "/x/bake"}
    monkeypatch.setattr(setup_update.shutil, "which", lambda name: present.get(name))
    with pytest.raises(SystemExit) as exit_info:
        bakebook._assert_tools()
    assert exit_info.value.code == 1


def test_assert_tools_passes_when_every_tool_resolves(
    bakebook: bakefile.MyBakebook, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(setup_update.shutil, "which", lambda name: f"/x/{name}")
    bakebook._assert_tools()
