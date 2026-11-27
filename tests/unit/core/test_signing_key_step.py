import json
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest
from bake import Context

from src.python.core import signing
from tests.unit.conftest import FakeCtx

NOW = datetime(2026, 11, 23, tzinfo=UTC)
TAG = signing.machine_tag("UUID-1")
TITLE = f"dotfiles: work-mac ({TAG})"
LIST_SECRET = "gpg --list-secret-keys --with-colons <a@b.c>"
LIST_GITHUB = "gh api --paginate --slurp user/gpg_keys"
UPLOAD = f"gh api user/gpg_keys -f name={TITLE} -f armored_public_key=ARMOR"


def _colons(expires: datetime | None) -> str:
    stamp = str(int(expires.timestamp())) if expires else ""
    return (
        f"sec:u:255:22:AAAA:1:{stamp}::u:::scSC:::+::ed25519:::0:\n"
        "fpr:::::::::FPR-AAAA:\n"
        "uid:u::::1::X::Ann Lee <a@b.c>::::::::::0:\n"
    )


def _api(id_: int, name: str, key_id: str, expires: datetime | None) -> dict[str, Any]:
    return {
        "id": id_,
        "name": name,
        "key_id": key_id,
        "expires_at": expires.isoformat() if expires else None,
        "emails": [{"email": "a@b.c", "verified": True}],
    }


def _key(fake_ctx: FakeCtx, interactive: bool = False) -> signing.SigningKey:
    return signing.SigningKey(
        cast("Context", fake_ctx),
        tag=TAG,
        name="work-mac",
        now=lambda: NOW,
        interactive=interactive,
    )


@pytest.fixture(autouse=True)
def machine(monkeypatch: pytest.MonkeyPatch, fake_ctx: FakeCtx) -> None:
    monkeypatch.setattr(signing.shutil, "which", lambda _name: "/usr/bin/gh")
    fake_ctx.stdout["git config --get user.signingkey"] = "<a@b.c>\n"
    fake_ctx.stdout["git config --get user.name"] = "Ann Lee\n"
    fake_ctx.stdout["gpg --armor --export FPR-AAAA"] = "ARMOR"
    fake_ctx.stdout[UPLOAD] = json.dumps(_api(9, TITLE, "AAAA", NOW))


def _have_key(fake_ctx: FakeCtx, expires: datetime | None) -> None:
    fake_ctx.stdout[LIST_SECRET] = _colons(expires)


def _github(fake_ctx: FakeCtx, *keys: dict[str, Any]) -> None:
    fake_ctx.stdout[LIST_GITHUB] = json.dumps([list(keys)])


def _cmds(fake_ctx: FakeCtx, prefix: str) -> list[str]:
    return [" ".join(c) for c in fake_ctx.commands if " ".join(c).startswith(prefix)]


def _writes(fake_ctx: FakeCtx) -> list[str]:
    return [c for c in _cmds(fake_ctx, "gh api") if c != LIST_GITHUB]


def test_does_nothing_without_a_git_signing_key(fake_ctx: FakeCtx) -> None:
    del fake_ctx.stdout["git config --get user.signingkey"]
    _key(fake_ctx).sync(create=True)
    assert _cmds(fake_ctx, "gpg") == []


def test_does_nothing_on_a_dry_run(fake_ctx: FakeCtx) -> None:
    fake_ctx.dry_run = True
    _key(fake_ctx).sync(create=True)
    assert fake_ctx.commands == []


def test_setup_creates_a_missing_key_that_expires(
    fake_ctx: FakeCtx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keys = iter([None, signing.parse_secret_key(_colons(NOW + timedelta(days=30)))])
    monkeypatch.setattr(
        signing.SigningKey, "local_key", lambda _self, _email: next(keys)
    )
    _github(fake_ctx)
    _key(fake_ctx).sync(create=True)
    assert _cmds(fake_ctx, "gpg --batch") == [
        "gpg --batch --passphrase  --quick-generate-key Ann Lee <a@b.c> ed25519 sign 30d"
    ]
    assert _writes(fake_ctx) == [UPLOAD]


def test_update_creates_no_key(fake_ctx: FakeCtx) -> None:
    fake_ctx.failing.add(LIST_SECRET)
    _key(fake_ctx).sync(create=False)
    assert _cmds(fake_ctx, "gpg --batch") == []
    assert _cmds(fake_ctx, "gh") == []


def test_a_key_with_time_left_is_not_renewed(fake_ctx: FakeCtx) -> None:
    expires = NOW + timedelta(days=20)
    _have_key(fake_ctx, expires)
    _github(fake_ctx, _api(1, TITLE, "AAAA", expires))
    _key(fake_ctx).sync(create=False)
    assert _cmds(fake_ctx, "gpg --batch") == []
    assert _writes(fake_ctx) == []


@pytest.mark.parametrize("days", [10, -5, None])
def test_a_key_due_or_expired_or_never_expiring_is_renewed_and_replaced(
    fake_ctx: FakeCtx, days: int | None
) -> None:
    old = NOW + timedelta(days=days) if days is not None else None
    _have_key(fake_ctx, old)
    _github(fake_ctx, _api(1, TITLE, "AAAA", old))
    _key(fake_ctx).sync(create=False)
    assert _cmds(fake_ctx, "gpg --batch") == [
        "gpg --batch --quick-set-expire FPR-AAAA 30d"
    ]


INCLUDES = r"git config --global --includes --get-regexp ^includeif\..*\.path$"
WORK_EMAIL = "git config --file /home/ann/.config/git/work.inc --get user.email"
ADD_UID = "gpg --batch --quick-add-uid FPR-AAAA Ann Lee <ann@work.example>"


def _work_include(fake_ctx: FakeCtx, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/home/ann")
    fake_ctx.stdout[INCLUDES] = "includeif.gitdir:~/work/.path ~/.config/git/work.inc\n"
    fake_ctx.stdout[WORK_EMAIL] = "ann@work.example\n"


def test_identity_emails_add_each_conditional_includes_email(
    fake_ctx: FakeCtx, monkeypatch: pytest.MonkeyPatch
) -> None:
    _work_include(fake_ctx, monkeypatch)
    assert _key(fake_ctx).identity_emails("<a@b.c>") == ["a@b.c", "ann@work.example"]


def test_identity_emails_is_the_signing_email_without_includes(
    fake_ctx: FakeCtx,
) -> None:
    assert _key(fake_ctx).identity_emails("<a@b.c>") == ["a@b.c"]


def test_a_key_missing_an_include_email_gains_it_and_is_reuploaded(
    fake_ctx: FakeCtx, monkeypatch: pytest.MonkeyPatch
) -> None:
    expires = NOW + timedelta(days=20)
    _work_include(fake_ctx, monkeypatch)
    keys = iter(
        [
            signing.parse_secret_key(_colons(expires)),
            signing.LocalKey(
                "AAAA", "FPR-AAAA", expires, frozenset({"a@b.c", "ann@work.example"})
            ),
        ]
    )
    monkeypatch.setattr(
        signing.SigningKey, "local_key", lambda _self, _email: next(keys)
    )
    _github(fake_ctx, _api(1, TITLE, "AAAA", expires))
    _key(fake_ctx).sync(create=False)
    assert _cmds(fake_ctx, "gpg --batch") == [ADD_UID]
    assert _writes(fake_ctx) == ["gh api -X DELETE user/gpg_keys/1", UPLOAD]


def test_a_key_holding_every_include_email_is_left_alone(
    fake_ctx: FakeCtx, monkeypatch: pytest.MonkeyPatch
) -> None:
    expires = NOW + timedelta(days=20)
    _work_include(fake_ctx, monkeypatch)
    fake_ctx.stdout[LIST_SECRET] = (
        _colons(expires) + "uid:u::::1::Y::Ann Lee <ann@work.example>::::::::::0:\n"
    )
    both = _api(1, TITLE, "AAAA", expires)
    both["emails"].append({"email": "ann@work.example", "verified": True})
    _github(fake_ctx, both)
    _key(fake_ctx).sync(create=False)
    assert _cmds(fake_ctx, "gpg --batch") == []
    assert _writes(fake_ctx) == []


def test_publish_replaces_this_machines_stale_entry_without_the_shell_token(
    fake_ctx: FakeCtx,
) -> None:
    local = signing.LocalKey("AAAA", "FPR-AAAA", NOW + timedelta(days=30))
    _github(fake_ctx, _api(1, TITLE, "AAAA", NOW + timedelta(days=10)))
    _key(fake_ctx).publish(local)
    assert _writes(fake_ctx) == ["gh api -X DELETE user/gpg_keys/1", UPLOAD]
    gh_envs = [e for c, e in zip(fake_ctx.commands, fake_ctx.envs) if c[0] == "gh"]
    assert all(
        e == {"GITHUB_TOKEN": None, "GH_TOKEN": None, "NO_COLOR": "1"} for e in gh_envs
    )


def test_publish_changes_nothing_when_github_is_current(fake_ctx: FakeCtx) -> None:
    local = signing.LocalKey("AAAA", "FPR-AAAA", NOW + timedelta(days=30))
    _github(fake_ctx, _api(1, TITLE, "AAAA", local.expires))
    _key(fake_ctx).publish(local)
    assert _writes(fake_ctx) == []


def test_publish_skips_when_gh_is_not_logged_in(fake_ctx: FakeCtx) -> None:
    fake_ctx.failing.add("gh auth status --hostname github.com")
    _key(fake_ctx).publish(signing.LocalKey("AAAA", "FPR-AAAA", NOW))
    assert _cmds(fake_ctx, "gh api") == []


def test_publish_without_the_scope_and_no_terminal_only_warns(
    fake_ctx: FakeCtx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_ctx.failing.add(LIST_GITHUB)
    refreshed: list[object] = []
    monkeypatch.setattr(signing.subprocess, "run", lambda *a, **k: refreshed.append(a))
    _key(fake_ctx).publish(signing.LocalKey("AAAA", "FPR-AAAA", NOW))
    assert refreshed == []
    assert _writes(fake_ctx) == []


def test_publish_without_the_scope_asks_gh_for_it_in_a_terminal(
    fake_ctx: FakeCtx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_ctx.failing.add(LIST_GITHUB)
    refreshed: list[list[str]] = []
    monkeypatch.setattr(
        signing.subprocess, "run", lambda cmd, **_k: refreshed.append(cmd)
    )
    _key(fake_ctx, interactive=True).publish(signing.LocalKey("AAAA", "FPR-AAAA", NOW))
    assert refreshed == [
        ["gh", "auth", "refresh", "-h", "github.com", "-s", "admin:gpg_key"]
    ]


@pytest.mark.parametrize(
    ("tty", "answer", "deleted"),
    [(True, True, True), (True, False, False), (False, True, False)],
)
def test_expired_keys_of_other_machines_are_deleted_only_when_confirmed(
    fake_ctx: FakeCtx,
    monkeypatch: pytest.MonkeyPatch,
    tty: bool,
    answer: bool,
    deleted: bool,
) -> None:
    local = signing.LocalKey("AAAA", "FPR-AAAA", NOW + timedelta(days=30))
    dead = _api(2, "dotfiles: old-mac (abcdef)", "CCCC", NOW - timedelta(days=1))
    _github(fake_ctx, _api(1, TITLE, "AAAA", local.expires), dead)
    monkeypatch.setattr(signing.typer, "confirm", lambda *_a, **_k: answer)
    _key(fake_ctx, interactive=tty).publish(local)
    assert _writes(fake_ctx) == (
        ["gh api -X DELETE user/gpg_keys/2"] if deleted else []
    )


def test_keys_without_the_dotfiles_title_are_never_deleted(
    fake_ctx: FakeCtx,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    local = signing.LocalKey("AAAA", "FPR-AAAA", NOW + timedelta(days=30))
    hand = _api(3, "old-laptop", "EEEE", NOW - timedelta(days=400))
    _github(fake_ctx, _api(1, TITLE, "AAAA", local.expires), hand)
    monkeypatch.setattr(signing.typer, "confirm", lambda *_a, **_k: True)
    _key(fake_ctx, interactive=True).publish(local)
    assert _writes(fake_ctx) == []
