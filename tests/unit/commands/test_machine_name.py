from pathlib import Path
from unittest.mock import patch

import pytest

from src.python import bakefile
from src.python.commands import machine
from src.python.core import machines, signing
from tests.unit.conftest import FakeCtx

IOREG = '    "IOPlatformSerialNumber" = "SERIAL0001"\n'


@pytest.fixture
def mac(fake_repo: Path, fake_ctx: FakeCtx, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv(machine.NAME_VAR, raising=False)
    monkeypatch.setattr(machine.shutil, "which", lambda _name: "/usr/sbin/ioreg")
    fake_ctx.stdout["ioreg -rd1 -c IOPlatformExpertDevice"] = IOREG
    lib = fake_repo / "private" / "src" / "lib"
    lib.mkdir(parents=True)
    return lib / "machines.toml"


def test_a_listed_machine_has_its_name(
    bakebook: bakefile.MyBakebook, mac: Path
) -> None:
    mac.write_text('"SERIAL0001" = { name = "work-mac" }\n')
    assert bakebook._machine_name() == "work-mac"


def test_an_unnamed_machine_fails_and_points_to_setup(
    bakebook: bakefile.MyBakebook, mac: Path
) -> None:
    del mac
    with pytest.raises(SystemExit, match="bake setup-dev"):
        bakebook._machine_name()


def test_the_env_var_names_a_machine_without_a_list(
    bakebook: bakefile.MyBakebook, mac: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del mac
    monkeypatch.setenv(machine.NAME_VAR, "ci")
    assert bakebook._machine_name() == "ci"
    assert bakebook._name_this_machine() == "ci"


def test_a_bad_env_var_name_fails(
    bakebook: bakefile.MyBakebook, mac: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del mac
    monkeypatch.setenv(machine.NAME_VAR, "My Mac")
    with pytest.raises(SystemExit, match=machine.NAME_VAR):
        bakebook._machine_name()


def test_setup_without_a_terminal_fails_for_an_unnamed_machine(
    bakebook: bakefile.MyBakebook, mac: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del mac
    monkeypatch.setattr(machine.sys.stdin, "isatty", lambda: False)
    with pytest.raises(SystemExit, match="in a terminal"):
        bakebook._name_this_machine()


def test_setup_asks_again_until_the_name_is_valid_then_saves_it(
    bakebook: bakefile.MyBakebook, mac: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mac.write_text('"OTHER" = { name = "home-mac" }\n')
    monkeypatch.setattr(machine.sys.stdin, "isatty", lambda: True)
    answers = iter(["Work Mac", "home-mac", "work-mac"])
    monkeypatch.setattr(machine.typer, "prompt", lambda *_a, **_k: next(answers))
    assert bakebook._name_this_machine() == "work-mac"
    assert machines.name(mac.parents[3], "SERIAL0001") == "work-mac"


@pytest.mark.parametrize(
    ("step", "create"), [("_setup_dotfiles", True), ("_update_dotfiles", False)]
)
def test_setup_and_update_title_the_key_with_the_machine_name(
    bakebook: bakefile.MyBakebook, mac: Path, step: str, create: bool
) -> None:
    mac.write_text('"SERIAL0001" = { name = "work-mac" }\n')
    with (
        patch.object(bakefile.MyBakebook, "_apply"),
        patch.object(signing.SigningKey, "for_this_machine") as key,
    ):
        getattr(bakebook, step)()
    key.assert_called_once_with(bakebook.ctx, "work-mac")
    key.return_value.sync.assert_called_once_with(create=create)


def test_update_fails_on_an_unnamed_machine(
    bakebook: bakefile.MyBakebook, mac: Path
) -> None:
    del mac
    with (
        patch.object(signing.SigningKey, "for_this_machine") as key,
        pytest.raises(SystemExit, match="bake setup-dev"),
    ):
        bakebook._update_dotfiles()
    key.assert_not_called()


def test_without_ioreg_the_linux_machine_id_is_the_key(
    bakebook: bakefile.MyBakebook, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(machine.shutil, "which", lambda _name: None)
    monkeypatch.setattr(machines, "linux_id", lambda: "abc123")
    assert bakebook._machine_id() == "abc123"
