from datetime import UTC, datetime, timedelta

from src.python.core import signing

NOW = datetime(2026, 11, 23, tzinfo=UTC)
TAG = signing.machine_tag("UUID-1")
TITLE = signing.title("work-mac", TAG)
LOCAL = signing.LocalKey("AAAA", "FPR-AAAA", NOW + timedelta(days=30))

COLONS = """\
sec:u:255:22:AAAA:1795425525:1803201525::u:::scSC:::+::ed25519:::0:
fpr:::::::::FPR-AAAA:
uid:u::::1795425525::X::Ann Lee <a@b.c>::::::::::0:
"""


def _gh(
    id_: int,
    name: str,
    key_id: str,
    expires: datetime | None,
    verified: bool = True,
    emails: frozenset[str] = frozenset(),
) -> signing.GithubKey:
    return signing.GithubKey(id_, name, key_id, expires, verified, emails)


def test_parse_secret_key_reads_id_fingerprint_and_expiry() -> None:
    key = signing.parse_secret_key(COLONS)
    assert key == signing.LocalKey(
        "AAAA",
        "FPR-AAAA",
        datetime.fromtimestamp(1803201525, UTC),
        frozenset({"a@b.c"}),
    )


def test_parse_secret_key_reads_every_live_uid_of_the_first_key_only() -> None:
    colons = COLONS + (
        "uid:u::::1795425525::Y::Ann Lee <ann@work.example>::::::::::0:\n"
        "uid:r::::1795425525::Z::Ann Lee <old@b.c>::::::::::0:\n"
        "sec:u:255:22:BBBB:1:2::u:::scSC:::+::ed25519:::0:\n"
        "fpr:::::::::FPR-BBBB:\n"
        "uid:u::::1::W::Bob <bob@b.c>::::::::::0:\n"
    )
    key = signing.parse_secret_key(colons)
    assert key is not None
    assert key.fingerprint == "FPR-AAAA"
    assert key.emails == {"a@b.c", "ann@work.example"}


def test_parse_secret_key_reads_a_key_that_never_expires() -> None:
    key = signing.parse_secret_key(COLONS.replace(":1803201525:", "::"))
    assert key is not None
    assert key.expires is None


def test_parse_secret_key_finds_nothing_in_empty_output() -> None:
    assert signing.parse_secret_key("") is None


def test_parse_ioreg_uuid() -> None:
    text = '  |   "IOPlatformUUID" = "12345678-ABCD"\n'
    assert signing.parse_ioreg_uuid(text) == "12345678-ABCD"
    assert signing.parse_ioreg_uuid("nothing") is None


def test_title_uses_the_machine_name_and_the_tag_round_trips() -> None:
    assert TITLE == f"dotfiles: work-mac ({TAG})"
    assert signing.tag_of(TITLE) == TAG
    assert signing.tag_of("old-laptop") is None


def test_machine_tag_is_stable_and_hides_the_id() -> None:
    assert signing.machine_tag("uuid-1\n") == TAG
    assert len(TAG) == 6
    assert "UUID" not in TAG


def test_renewal_is_due_only_in_the_second_half_of_the_lifetime() -> None:
    def key(days: float | None) -> signing.LocalKey:
        expires = None if days is None else NOW + timedelta(days=days)
        return signing.LocalKey("A", "F", expires)

    assert not signing.needs_renewal(key(16), NOW)
    assert signing.needs_renewal(key(14), NOW)
    assert signing.needs_renewal(key(-3), NOW)
    assert signing.needs_renewal(key(None), NOW)


def test_github_key_reads_the_api_shape() -> None:
    key = signing.github_key(
        {
            "id": 7,
            "name": TITLE,
            "key_id": "AAAA",
            "expires_at": "2027-02-21T11:00:00.000+07:00",
            "emails": [{"email": "a@b.c", "verified": False}],
        }
    )
    assert key == _gh(
        7,
        TITLE,
        "AAAA",
        datetime(2027, 2, 21, 4, tzinfo=UTC),
        verified=False,
        emails=frozenset({"a@b.c"}),
    )


def test_github_key_is_verified_only_when_every_email_is() -> None:
    def key(*verified: bool) -> signing.GithubKey:
        emails = [{"email": f"{i}@b.c", "verified": v} for i, v in enumerate(verified)]
        return signing.github_key(
            {"id": 1, "name": TITLE, "key_id": "AAAA", "emails": emails}
        )

    assert key(True, True).email_verified
    assert not key(True, False).email_verified
    assert not key().email_verified


def test_plan_uploads_when_github_has_no_key_for_this_machine() -> None:
    plan = signing.plan([], LOCAL, TITLE, NOW)
    assert plan == signing.Plan(upload=True, delete=[], expired=[], unmanaged=[])


def test_plan_changes_nothing_when_github_holds_the_current_key() -> None:
    current = _gh(1, TITLE, "AAAA", LOCAL.expires)
    plan = signing.plan([current], LOCAL, TITLE, NOW)
    assert not plan.upload
    assert plan.delete == []


def test_plan_replaces_the_github_copy_when_the_key_gained_an_email() -> None:
    local = signing.LocalKey(
        "AAAA", "FPR-AAAA", LOCAL.expires, frozenset({"a@b.c", "ann@work.example"})
    )
    stale = _gh(1, TITLE, "AAAA", LOCAL.expires, emails=frozenset({"a@b.c"}))
    plan = signing.plan([stale], local, TITLE, NOW)
    assert plan.upload
    assert plan.delete == [stale]


def test_plan_replaces_this_machines_entry_after_a_renewal() -> None:
    stale = _gh(1, TITLE, "AAAA", NOW + timedelta(days=10))
    plan = signing.plan([stale], LOCAL, TITLE, NOW)
    assert plan.upload
    assert plan.delete == [stale]


def test_plan_replaces_an_older_key_from_the_same_machine() -> None:
    old = _gh(1, signing.title("old-name", TAG), "BBBB", NOW - timedelta(days=1))
    plan = signing.plan([old], LOCAL, TITLE, NOW)
    assert plan.upload
    assert plan.delete == [old]
    assert plan.expired == []


def test_plan_retitles_the_same_key_after_a_rename() -> None:
    renamed = _gh(1, "something else", "AAAA", LOCAL.expires)
    plan = signing.plan([renamed], LOCAL, TITLE, NOW)
    assert plan.upload
    assert plan.delete == [renamed]


def test_plan_offers_other_machines_expired_keys_and_leaves_live_ones() -> None:
    other = signing.machine_tag("UUID-2")
    dead = _gh(2, signing.title("old-mac", other), "CCCC", NOW - timedelta(days=1))
    live = _gh(3, signing.title("linux", "abcdef"), "DDDD", NOW + timedelta(days=30))
    plan = signing.plan([dead, live], LOCAL, TITLE, NOW)
    assert plan.expired == [dead]
    assert live not in plan.delete


def test_plan_never_touches_keys_without_the_dotfiles_title() -> None:
    hand = _gh(4, "old-laptop", "EEEE", NOW - timedelta(days=400))
    plan = signing.plan([hand], LOCAL, TITLE, NOW)
    assert plan.unmanaged == [hand]
    assert plan.delete == []
    assert plan.expired == []


def test_status_names_this_machine_live_expired_and_never_expiring_keys() -> None:
    mine = _gh(1, TITLE, "AAAA", NOW + timedelta(days=30))
    live = _gh(2, "dotfiles: linux (abcdef)", "BBBB", NOW + timedelta(days=5))
    dead = _gh(3, "dotfiles: old-mac (123456)", "CCCC", NOW - timedelta(days=1))
    old = _gh(4, "old-laptop", "DDDD", None)
    keys = [mine, live, dead, old]
    assert [signing.status(k, "AAAA", NOW) for k in keys] == [
        "this machine",
        "live",
        "expired",
        "no expiry",
    ]
