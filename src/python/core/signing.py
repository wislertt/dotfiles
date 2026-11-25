import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import typer
from bake import Context, console

from src.python.core import machines

# Each machine's key expires unless Update renews it, so a machine no longer in use drops off GitHub
LIFETIME_DAYS = 30
TITLE_PREFIX = "dotfiles: "
GH_TOKEN_VARS = ("GITHUB_TOKEN", "GH_TOKEN")
_TITLE = re.compile(rf"^{re.escape(TITLE_PREFIX)}.* \(([0-9a-f]{{6}})\)$")
_IOREG_UUID = re.compile(r'"IOPlatformUUID" = "([^"]+)"')


@dataclass(frozen=True)
class LocalKey:
    key_id: str
    fingerprint: str
    expires: datetime | None


@dataclass(frozen=True)
class GithubKey:
    id: int
    name: str
    key_id: str
    expires: datetime | None
    email_verified: bool


@dataclass(frozen=True)
class Plan:
    upload: bool
    delete: list[GithubKey]  # this machine's stale entries
    expired: list[GithubKey]  # other machines' dotfiles keys that have expired
    unmanaged: list[GithubKey]  # keys without the dotfiles title: never touched


def parse_secret_key(colons: str) -> LocalKey | None:
    """The first secret key in `gpg --list-secret-keys --with-colons` output."""
    sec: list[str] | None = None
    for line in colons.splitlines():
        fields = line.split(":")
        if fields[0] == "sec" and sec is None:
            sec = fields
        elif fields[0] == "fpr" and sec is not None:
            expires = (
                datetime.fromtimestamp(int(sec[6]), UTC) if sec[6].strip() else None
            )
            return LocalKey(sec[4], fields[9], expires)
    return None


def parse_ioreg_uuid(text: str) -> str | None:
    match = _IOREG_UUID.search(text)
    return match.group(1) if match else None


def machine_tag(machine_id: str) -> str:
    # Hashed, so the hardware ID itself never leaves the machine
    return hashlib.sha256(machine_id.strip().lower().encode()).hexdigest()[:6]


def title(name: str, tag: str) -> str:
    return f"{TITLE_PREFIX}{name} ({tag})"


def tag_of(name: str) -> str | None:
    match = _TITLE.match(name)
    return match.group(1) if match else None


def needs_renewal(key: LocalKey, now: datetime) -> bool:
    if key.expires is None:
        return True
    return key.expires - now < timedelta(days=LIFETIME_DAYS / 2)


def github_key(data: Mapping[str, Any]) -> GithubKey:
    expires = data.get("expires_at")
    return GithubKey(
        id=int(data["id"]),
        name=str(data.get("name") or ""),
        key_id=str(data["key_id"]),
        expires=datetime.fromisoformat(expires) if expires else None,
        email_verified=any(e.get("verified") for e in data.get("emails") or []),
    )


def _same_second(a: datetime | None, b: datetime | None) -> bool:
    if a is None or b is None:
        return a is b
    return int(a.timestamp()) == int(b.timestamp())


def plan(
    keys: Iterable[GithubKey], local: LocalKey, wanted_title: str, now: datetime
) -> Plan:
    """What to change on GitHub so it holds exactly this machine's current key."""
    keys = list(keys)
    tag = tag_of(wanted_title)
    mine = [k for k in keys if k.key_id == local.key_id or tag_of(k.name) == tag]
    current = next(
        (
            k
            for k in mine
            if k.key_id == local.key_id
            and k.name == wanted_title
            and _same_second(k.expires, local.expires)
        ),
        None,
    )
    return Plan(
        upload=current is None,
        delete=[k for k in mine if k is not current],
        expired=[
            k
            for k in keys
            if k not in mine and tag_of(k.name) and k.expires and k.expires <= now
        ],
        unmanaged=[k for k in keys if k not in mine and tag_of(k.name) is None],
    )


def status(key: GithubKey, local_key_id: str | None, now: datetime) -> str:
    if key.key_id == local_key_id:
        return "this machine"
    if key.expires is None:
        return "no expiry"
    return "expired" if key.expires <= now else "live"


def read_machine_tag(ctx: Context) -> str | None:
    if sys.platform == "darwin":
        out = ctx.run(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            capture_output=True,
            stream=False,
            echo=False,
            check=False,
        ).stdout
        raw = parse_ioreg_uuid(out)
    else:
        raw = machines.linux_id()
    return machine_tag(raw) if raw else None


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SigningKey:
    """A machine's Signing key: create it, renew it, and keep GitHub holding exactly one copy."""

    def __init__(
        self,
        ctx: Context,
        *,
        tag: str | None,
        name: str | None,
        now: Callable[[], datetime] = _utcnow,
        interactive: bool = False,
        confirm_delete: Callable[[GithubKey], bool] | None = None,
        gnupghome: Path | None = None,
    ) -> None:
        self.ctx = ctx
        self.tag = tag
        self.name = name  # None when only reading GitHub's keys, as Tidy does
        self.now = now
        self.interactive = interactive
        self.confirm_delete = confirm_delete or self._ask_delete
        self.gpg_env = {"GNUPGHOME": str(gnupghome)} if gnupghome else None

    @classmethod
    def for_this_machine(cls, ctx: Context, name: str | None = None) -> SigningKey:
        return cls(
            ctx,
            tag=read_machine_tag(ctx),
            name=name,
            interactive=sys.stdin.isatty(),
        )

    def sync(self, create: bool) -> LocalKey | None:
        """Setup passes create=True; Update only renews and publishes. Needs the git include Apply links."""
        if self.ctx.dry_run:
            return None
        email = self._git_config("user.signingkey")
        if not email:
            return None
        local = self.local_key(email)
        if local is None:
            if not create:
                console.warning(
                    "No GPG signing key on this machine; run `bake setup-dev`"
                )
                return None
            self._create(email)
            local = self.local_key(email)
            if local is None:
                raise SystemExit("GPG signing key was not created")
            console.success("GPG signing key created")
        elif needs_renewal(local, self.now()):
            # Same key, new date: gpg can extend a key even after it has expired
            self.gpg("--batch", "--quick-set-expire", local.fingerprint, self._expiry())
            local = self.local_key(email) or local
            console.success("GPG signing key renewed")
        else:
            console.success("GPG signing key present")
        self.publish(local)
        return local

    def local_key(self, email: str) -> LocalKey | None:
        result = self.gpg("--list-secret-keys", "--with-colons", email, check=False)
        return parse_secret_key(result.stdout) if result.returncode == 0 else None

    def publish(self, local: LocalKey) -> None:
        if self.tag is None:
            console.warning("No machine ID, so the GPG key is not uploaded to GitHub")
            return
        keys = self.github_keys()
        if keys is None:
            return
        if self.name is None:
            raise SystemExit("No machine name, so the GPG key cannot be titled")
        wanted = title(self.name, self.tag)
        changes = plan(keys, local, wanted, self.now())
        for key in changes.delete:
            self.delete_github_key(key)
        if changes.upload:
            armored = self.gpg("--armor", "--export", local.fingerprint).stdout
            ours = github_key(
                json.loads(
                    self._gh(
                        "api",
                        "user/gpg_keys",
                        "-f",
                        f"name={wanted}",
                        "-f",
                        f"armored_public_key={armored}",
                    )
                )
            )
            console.success(f"GPG key uploaded to GitHub as {wanted!r}")
        else:
            ours = next(k for k in keys if k not in changes.delete and k.name == wanted)
            console.success("GPG key on GitHub is current")
        if not ours.email_verified:
            console.warning(
                "The key's email is not verified on GitHub, so its commits show as Unverified"
            )
        for key in changes.expired:
            if self.confirm_delete(key):
                self.delete_github_key(key)
                console.success(f"Deleted {key.name!r}")
            else:
                console.warning(f"Expired GitHub GPG key kept: {key.name!r}")
        for key in changes.unmanaged:
            console.info(
                f"GitHub GPG key not managed by dotfiles, left alone: {key.name or key.key_id}"
            )

    def github_keys(self) -> list[GithubKey] | None:
        if shutil.which("gh") is None:
            console.warning("gh is not installed, so the GPG key is not uploaded")
            return None
        if self._gh_run("auth", "status", "--hostname", "github.com").returncode:
            console.warning(
                "gh is not logged in, so the GPG key is not uploaded; run `gh auth login`, then `bake update`"
            )
            return None
        listing = ("api", "--paginate", "--slurp", "user/gpg_keys")
        result = self._gh_run(*listing)
        if result.returncode and self.interactive:
            # The login lacks admin:gpg_key, and the browser approves it once per machine
            subprocess.run(
                ["gh", "auth", "refresh", "-h", "github.com", "-s", "admin:gpg_key"],
                env={k: v for k, v in os.environ.items() if k not in GH_TOKEN_VARS},
                check=False,
            )
            result = self._gh_run(*listing)
        if result.returncode:
            console.warning(
                "gh lacks the admin:gpg_key scope, so the GPG key is not uploaded; "
                "run `gh auth refresh -h github.com -s admin:gpg_key`, then `bake update`"
            )
            return None
        return [github_key(k) for page in json.loads(result.stdout) for k in page]

    def local_key_id(self) -> str | None:
        email = self._git_config("user.signingkey")
        local = self.local_key(email) if email else None
        return local.key_id if local else None

    def delete_github_key(self, key: GithubKey) -> None:
        self._gh("api", "-X", "DELETE", f"user/gpg_keys/{key.id}")

    def gpg(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self.ctx.run(
            ["gpg", *args],
            env=self.gpg_env,
            capture_output=True,
            stream=False,
            echo=False,
            check=check,
        )

    def _create(self, email: str) -> None:
        name = self._git_config("user.name")
        # No passphrase, so no pinentry: commits from editors and agents have no terminal to prompt in
        self.gpg(
            "--batch",
            "--passphrase",
            "",
            "--quick-generate-key",
            f"{name} {email}",
            "ed25519",
            "sign",
            self._expiry(),
        )

    def _expiry(self) -> str:
        return f"{LIFETIME_DAYS}d"

    def _ask_delete(self, key: GithubKey) -> bool:
        return self.interactive and typer.confirm(
            f"Delete expired GitHub GPG key {key.name!r}?", default=True
        )

    def _gh_run(self, *args: str) -> subprocess.CompletedProcess[str]:
        # The stored gh login, not the shell's GITHUB_TOKEN, which may predate the scope.
        # bake runs commands in a pty, where gh would colour its JSON
        return self.ctx.run(
            ["gh", *args],
            env={**dict.fromkeys(GH_TOKEN_VARS), "NO_COLOR": "1"},
            capture_output=True,
            stream=False,
            echo=False,
            check=False,
        )

    def _gh(self, *args: str) -> str:
        result = self._gh_run(*args)
        if result.returncode:
            raise SystemExit(f"gh {args[0]} failed: {result.stderr.strip()}")
        return result.stdout

    def _git_config(self, name: str) -> str:
        return self.ctx.run(
            ["git", "config", "--get", name],
            capture_output=True,
            stream=False,
            echo=False,
            check=False,
        ).stdout.strip()
