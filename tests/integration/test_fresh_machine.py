import json
from pathlib import Path

from tests.integration.conftest import Machine


def test_public_clone_applies_and_a_second_apply_changes_nothing(
    public_machine: Machine,
) -> None:
    first = public_machine.apply()
    assert first.returncode == 0, first.stderr
    links = public_machine.links()
    assert links
    assert all((public_machine.home / rel).exists() for rel in links)

    second = public_machine.apply()
    assert second.returncode == 0, second.stderr
    assert public_machine.links() == links


def test_apply_links_the_repo_as_the_global_bake_directory(
    public_machine: Machine,
) -> None:
    result = public_machine.apply()
    assert result.returncode == 0, result.stderr
    link = public_machine.home / ".config" / "bake"
    assert link.resolve() == public_machine.repo.resolve()
    assert (link / "bakefile.py").is_file()


def test_existing_regular_file_is_refused_named_and_left_untouched(
    public_machine: Machine,
) -> None:
    target = Path(".zshenv")
    (public_machine.home / target).write_text("keep")

    result = public_machine.apply()

    assert result.returncode != 0
    assert str(target) in result.stderr
    assert (public_machine.home / target).read_text() == "keep"
    assert not (public_machine.home / target).is_symlink()


def test_private_groups_load_when_the_private_companion_is_present(
    private_machine: Machine,
) -> None:
    result = private_machine.apply("-E", "private")
    assert result.returncode == 0, result.stderr

    links = private_machine.links()
    for source in (private_machine.repo / "private" / "src").rglob("*"):
        if not source.is_file():
            continue
        group, _, rest = (
            source.relative_to(private_machine.repo / "private" / "src")
            .as_posix()
            .partition("/")
        )
        if group in ("lib", "merge"):  # read from the repo, never linked
            assert source not in links.values()
            continue
        base = {"bin": Path(".local/bin"), "config": Path(".config"), "home": Path()}[
            group
        ]
        assert links[base / rest] == source


def test_two_groups_claiming_one_target_are_rejected(private_machine: Machine) -> None:
    clash = private_machine.repo / "private" / "src" / "home" / ".zshenv"
    clash.write_text("clash")

    result = private_machine.apply("-E", "private")

    assert result.returncode != 0
    assert "conflicting" in result.stderr


def _settings(machine: Machine) -> Path:
    return machine.home / ".claude" / "settings.json"


def _owned(machine: Machine, name: str) -> dict[str, object]:
    return json.loads(
        (machine.repo / "private" / "src" / "merge" / ".claude" / name).read_text()
    )


def test_owned_claude_keys_merge_in_beside_the_apps_own_keys(
    private_machine: Machine,
) -> None:
    enforced = _owned(private_machine, "settings.json")
    settings = _settings(private_machine)
    settings.parent.mkdir()
    settings.write_text(json.dumps({"hooks": {"Stop": []}}))

    result = private_machine.apply("-E", "private")

    assert result.returncode == 0, result.stderr
    merged = json.loads(settings.read_text())
    assert merged["hooks"] == {"Stop": []}
    assert {k: merged[k] for k in enforced} == enforced
    assert _owned(private_machine, "settings.defaults.json").keys() <= merged.keys()


def test_apply_keeps_what_the_app_changed_and_a_rerun_changes_nothing(
    private_machine: Machine,
) -> None:
    enforced = _owned(private_machine, "settings.json")
    default = next(iter(_owned(private_machine, "settings.defaults.json")))
    assert private_machine.apply("-E", "private").returncode == 0
    settings = _settings(private_machine)
    app = json.loads(settings.read_text())
    app.update({default: "app-picked", "appKey": 1, "statusLine": "app-picked"})
    settings.write_text(json.dumps(app))

    assert private_machine.apply("-E", "private").returncode == 0
    once = settings.read_text()
    assert private_machine.apply("-E", "private").returncode == 0

    assert settings.read_text() == once
    merged = json.loads(once)
    assert merged[default] == "app-picked"
    assert merged["appKey"] == 1
    assert merged["statusLine"] == enforced["statusLine"]


def test_owned_zed_keys_merge_into_a_settings_file_with_comments(
    private_machine: Machine,
) -> None:
    settings = private_machine.home / ".config" / "zed" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('// Zed rewrites this\n{\n  "app_only_key": true\n}\n')

    result = private_machine.apply("-E", "private")

    assert result.returncode == 0, result.stderr
    text = settings.read_text()
    assert '"app_only_key": true' in text
    assert text != '// Zed rewrites this\n{\n  "app_only_key": true\n}\n'
    assert not settings.is_symlink()


def test_agent_home_files_are_linked_from_the_private_repo(
    private_machine: Machine,
) -> None:
    result = private_machine.apply("-E", "private")
    assert result.returncode == 0, result.stderr

    links = private_machine.links()
    home = private_machine.repo / "private" / "src" / "home"
    for rel in (Path(".claude/rules/user-rules.md"), Path(".claude/statusline.sh")):
        assert links[rel] == home / rel
