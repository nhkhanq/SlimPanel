from __future__ import annotations

import re
import shutil
from pathlib import Path

from app.config import settings
from app.errors import NotFound, PanelError
from app.services import shell

DIRECTIVE = re.compile(r"^\s*#?\s*([A-Za-z]\w*)\s+(.*?)\s*$")

# The sshd_config knobs a panel exposes, with the values the UI may set.
EDITABLE = {
    "Port": None,
    "PermitRootLogin": {"yes", "no", "prohibit-password", "forced-commands-only"},
    "PasswordAuthentication": {"yes", "no"},
    "PubkeyAuthentication": {"yes", "no"},
    "PermitEmptyPasswords": {"yes", "no"},
    "X11Forwarding": {"yes", "no"},
    "ClientAliveInterval": None,
    "ClientAliveCountMax": None,
    "MaxAuthTries": None,
    "AllowTcpForwarding": {"yes", "no"},
    "UseDNS": {"yes", "no"},
}

DEFAULTS = {
    "Port": "22",
    "PermitRootLogin": "prohibit-password",
    "PasswordAuthentication": "yes",
    "PubkeyAuthentication": "yes",
    "PermitEmptyPasswords": "no",
    "X11Forwarding": "no",
    "ClientAliveInterval": "0",
    "ClientAliveCountMax": "3",
    "MaxAuthTries": "6",
    "AllowTcpForwarding": "yes",
    "UseDNS": "no",
}


def config_path() -> Path:
    path = Path(settings.sshd_config)
    if not path.is_file():
        raise NotFound(f"{path} not found")
    return path


def service_name() -> str:
    configured = (settings.sshd_service or "auto").strip()
    if configured and configured != "auto":
        return configured
    for name in ("sshd", "ssh"):
        if shell.run([settings.systemctl_bin, "cat", name], timeout=10).ok:
            return name
    return "sshd"


def read_config() -> dict:
    path = config_path()
    text = path.read_text(errors="replace")

    values = dict(DEFAULTS)
    for line in text.splitlines():
        match = DIRECTIVE.match(line)
        if not match or line.lstrip().startswith("#"):
            continue
        key, value = match.group(1), match.group(2)
        if key in EDITABLE:
            values[key] = value.split()[0] if value.split() else value

    return {
        "path": str(path),
        "content": text,
        "values": values,
        "editable": {k: sorted(v) if v else [] for k, v in EDITABLE.items()},
        "service": service_name(),
        "running": shell.run([settings.systemctl_bin, "is-active", service_name()], timeout=10).stdout.strip()
        == "active",
    }


def set_values(values: dict[str, str]) -> dict:
    """Patch sshd_config, keeping a backup and refusing a config sshd rejects."""
    path = config_path()
    for key, value in values.items():
        if key not in EDITABLE:
            raise PanelError(f"{key} is not an editable sshd option")
        allowed = EDITABLE[key]
        if allowed and value not in allowed:
            raise PanelError(f"{key} must be one of {', '.join(sorted(allowed))}")
        if allowed is None and not str(value).isdigit():
            raise PanelError(f"{key} must be a number")
        if key == "Port" and not 1 <= int(value) <= 65535:
            raise PanelError("Port out of range")

    original = path.read_text(errors="replace")
    lines = original.splitlines()
    seen: set[str] = set()

    for index, line in enumerate(lines):
        match = DIRECTIVE.match(line)
        if not match or line.lstrip().startswith("#"):
            continue
        key = match.group(1)
        if key not in values:
            continue
        if key in seen:
            # sshd honours the first occurrence, so later ones have to go.
            lines[index] = f"# {line}  # superseded by SlimPanel"
        else:
            lines[index] = f"{key} {values[key]}"
            seen.add(key)

    trailer = [f"{key} {value}" for key, value in values.items() if key not in seen]
    if trailer:
        lines += ["", "# Added by SlimPanel"] + trailer

    path.with_suffix(path.suffix + ".slimpanel.bak").write_text(original)
    path.write_text("\n".join(lines) + "\n")

    check = test_config()
    if not check.ok:
        path.write_text(original)
        raise PanelError("sshd rejected the new configuration, rolled back", check.output)
    return read_config()


def write_config(content: str) -> dict:
    path = config_path()
    original = path.read_text(errors="replace")
    path.with_suffix(path.suffix + ".slimpanel.bak").write_text(original)
    path.write_text(content)
    check = test_config()
    if not check.ok:
        path.write_text(original)
        raise PanelError("sshd rejected the new configuration, rolled back", check.output)
    return read_config()


def test_config() -> shell.Result:
    binary = shutil.which("sshd") or "/usr/sbin/sshd"
    return shell.run([binary, "-t", "-f", str(config_path())], timeout=20)


def restart() -> shell.Result:
    return shell.run([settings.systemctl_bin, "restart", service_name()], timeout=60)


def authorized_keys_path(user: str = "root") -> Path:
    import pwd

    try:
        home = Path(pwd.getpwnam(user).pw_dir)
    except KeyError as exc:
        raise NotFound(f"No such user: {user}") from exc
    return home / ".ssh" / "authorized_keys"


def list_keys(user: str = "root") -> list[dict]:
    path = authorized_keys_path(user)
    try:
        if not path.is_file():
            return []
        body = path.read_text(errors="replace")
    except OSError as exc:
        raise PanelError(f"Cannot read {path}: {exc}") from exc

    rows = []
    for index, line in enumerate(body.splitlines()):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        rows.append(
            {
                "index": index,
                "type": parts[0] if parts else "",
                "comment": " ".join(parts[2:]) if len(parts) > 2 else "",
                "fingerprint": _fingerprint(stripped),
            }
        )
    return rows


def _fingerprint(line: str) -> str:
    import base64
    import hashlib

    parts = line.split()
    if len(parts) < 2:
        return ""
    try:
        blob = base64.b64decode(parts[1])
    except ValueError:
        return ""
    digest = base64.b64encode(hashlib.sha256(blob).digest()).decode().rstrip("=")
    return f"SHA256:{digest}"


def add_key(public_key: str, user: str = "root") -> list[dict]:
    cleaned = public_key.strip()
    if not cleaned or "\n" in cleaned:
        raise PanelError("Paste a single public key line")
    if not cleaned.split()[0].startswith(("ssh-", "ecdsa-", "sk-")):
        raise PanelError("That does not look like an SSH public key")

    path = authorized_keys_path(user)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    existing = path.read_text(errors="replace") if path.is_file() else ""
    if cleaned.split()[1] in existing:
        raise PanelError("That key is already authorised")
    path.write_text(existing.rstrip("\n") + ("\n" if existing.strip() else "") + cleaned + "\n")
    path.chmod(0o600)
    return list_keys(user)


def remove_key(index: int, user: str = "root") -> list[dict]:
    path = authorized_keys_path(user)
    if not path.is_file():
        raise NotFound("No authorized_keys file")
    lines = path.read_text(errors="replace").splitlines()
    if not 0 <= index < len(lines):
        raise NotFound("Key not found")
    del lines[index]
    path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return list_keys(user)


def login_history(limit: int = 100) -> list[dict]:
    """Recent successful logins, from `last`."""
    result = shell.run(["last", "-n", str(limit), "-F"], timeout=20)
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0] in {"wtmp", "reboot"}:
            continue
        rows.append({"user": parts[0], "tty": parts[1], "from": parts[2], "when": " ".join(parts[3:])})
    return rows


def failed_logins(limit: int = 200) -> list[dict]:
    """Failed SSH attempts grouped by address — the panel's fail2ban-lite view."""
    counts: dict[tuple[str, str], int] = {}
    for candidate in ("/var/log/auth.log", "/var/log/secure"):
        path = Path(candidate)
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for line in text.splitlines()[-20000:]:
            if "Failed password" not in line and "Invalid user" not in line:
                continue
            ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", line)
            user_match = re.search(r"(?:for(?: invalid user)?|Invalid user) (\S+)", line)
            if not ip_match:
                continue
            key = (ip_match.group(1), user_match.group(1) if user_match else "")
            counts[key] = counts.get(key, 0) + 1
        break
    rows = [{"ip": ip, "username": user, "attempts": n} for (ip, user), n in counts.items()]
    rows.sort(key=lambda row: row["attempts"], reverse=True)
    return rows[:limit]
