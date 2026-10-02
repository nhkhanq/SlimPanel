from __future__ import annotations

import ipaddress
import os
import re
import stat
from datetime import timedelta
from pathlib import Path

from sqlmodel import Session, col, select

from app.config import settings
from app.models import LoginAttempt, LoginLog, Site, utcnow
from app.services import firewall, shell, sshd

RISKY_PERMISSION = 0o777
SUSPICIOUS_PHP = re.compile(
    rb"(eval\s*\(\s*(base64_decode|gzinflate|str_rot13)|assert\s*\(\s*\$_|"
    rb"\$_(POST|GET|REQUEST|COOKIE)\s*\[[^\]]*\]\s*\(|preg_replace\s*\(\s*['\"].*/e['\"]|"
    rb"system\s*\(\s*\$_|shell_exec\s*\(\s*\$_|passthru\s*\(\s*\$_)",
    re.I,
)


# ------------------------------------------------------- panel login throttling


def record_attempt(session: Session, ip: str, username: str) -> None:
    session.add(LoginAttempt(ip=ip, username=username))
    session.commit()


def clear_attempts(session: Session, ip: str) -> None:
    for row in session.exec(select(LoginAttempt).where(LoginAttempt.ip == ip)).all():
        session.delete(row)
    session.commit()


def attempts_since(session: Session, ip: str) -> int:
    cutoff = utcnow() - timedelta(minutes=settings.login_block_minutes)
    rows = session.exec(
        select(LoginAttempt).where(
            LoginAttempt.ip == ip, col(LoginAttempt.created_at) >= cutoff
        )
    ).all()
    return len(rows)


def is_blocked(session: Session, ip: str) -> tuple[bool, int]:
    """Whether this address has burnt through its login attempts."""
    if not ip or settings.login_max_attempts <= 0:
        return False, 0
    used = attempts_since(session, ip)
    remaining = max(0, settings.login_max_attempts - used)
    return used >= settings.login_max_attempts, remaining


def blocked_addresses(session: Session) -> list[dict]:
    cutoff = utcnow() - timedelta(minutes=settings.login_block_minutes)
    counts: dict[str, dict] = {}
    for row in session.exec(
        select(LoginAttempt).where(col(LoginAttempt.created_at) >= cutoff)
    ).all():
        entry = counts.setdefault(row.ip, {"ip": row.ip, "attempts": 0, "last": row.created_at,
                                           "usernames": set()})
        entry["attempts"] += 1
        entry["last"] = max(entry["last"], row.created_at)
        if row.username:
            entry["usernames"].add(row.username)

    rows = []
    for entry in counts.values():
        rows.append(
            {
                "ip": entry["ip"],
                "attempts": entry["attempts"],
                "last": entry["last"],
                "usernames": sorted(entry["usernames"]),
                "blocked": entry["attempts"] >= settings.login_max_attempts,
            }
        )
    rows.sort(key=lambda row: row["attempts"], reverse=True)
    return rows


def ip_allowed(session: Session, ip: str) -> bool:
    """Panel-scope allow/deny, plus the static allowlist in the config file."""
    if not ip:
        return True
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return True

    allow, deny = firewall.panel_blocklist(session)
    for entry in deny:
        try:
            if address in ipaddress.ip_network(entry, strict=False):
                return False
        except ValueError:
            continue

    configured = [entry for entry in settings.panel_ip_allowlist if entry.strip()]
    whitelist = set(configured) | allow
    if not whitelist:
        return True
    for entry in whitelist:
        try:
            if address in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            continue
    return False


# ------------------------------------------------------------------ risk audit


def _check(name: str, ok: bool, detail: str, severity: str = "medium", fix: str = "") -> dict:
    return {"name": name, "ok": ok, "detail": detail, "severity": severity, "fix": fix}


def audit(session: Session) -> dict:
    """The security baseline scan: cheap checks a panel can act on."""
    checks: list[dict] = []

    try:
        ssh = sshd.read_config()
        values = ssh["values"]
        checks.append(
            _check(
                "SSH root login",
                values.get("PermitRootLogin") in {"no", "prohibit-password", "forced-commands-only"},
                f"PermitRootLogin is {values.get('PermitRootLogin')}",
                "high",
                "Set PermitRootLogin to prohibit-password on the Security page",
            )
        )
        checks.append(
            _check(
                "SSH password login",
                values.get("PasswordAuthentication") == "no",
                f"PasswordAuthentication is {values.get('PasswordAuthentication')}",
                "medium",
                "Add an SSH key, then turn password authentication off",
            )
        )
        checks.append(
            _check(
                "SSH port",
                values.get("Port") != "22",
                f"sshd listens on port {values.get('Port')}",
                "low",
                "Move SSH off port 22 to cut scanner noise",
            )
        )
        checks.append(
            _check(
                "Empty SSH passwords",
                values.get("PermitEmptyPasswords") == "no",
                f"PermitEmptyPasswords is {values.get('PermitEmptyPasswords')}",
                "high",
                "Set PermitEmptyPasswords to no",
            )
        )
    except Exception as exc:  # a missing sshd_config should not fail the audit
        checks.append(_check("SSH configuration", False, f"Could not read sshd_config: {exc}", "low"))

    status = firewall.status()
    checks.append(
        _check(
            "Firewall",
            status["active"],
            f"{status['backend']} is {'active' if status['active'] else 'inactive'}",
            "high",
            "Turn the firewall on from the Security page and open only what you serve",
        )
    )

    checks.append(
        _check(
            "Panel entry path",
            bool(settings.entry_path),
            "The panel is served from a secret prefix" if settings.entry_path
            else "The panel is served from /",
            "medium",
            'Set "entry_path" in slimpanel.json',
        )
    )
    checks.append(
        _check(
            "Panel IP allowlist",
            bool(settings.panel_ip_allowlist),
            f"{len(settings.panel_ip_allowlist)} entries"
            if settings.panel_ip_allowlist
            else "Any address may reach the login page",
            "medium",
            "Add your own address under Security → Panel access",
        )
    )

    from app.models import User

    users = list(session.exec(select(User)).all())
    checks.append(
        _check(
            "Two-factor authentication",
            all(user.totp_enabled for user in users) and bool(users),
            f"{sum(1 for u in users if u.totp_enabled)}/{len(users)} accounts have TOTP",
            "high",
            "Enable TOTP under Settings → Account",
        )
    )

    if settings.mysql_user == "root" and not settings.mysql_password:
        checks.append(
            _check("MySQL root password", False, "No MySQL password is configured", "high",
                   'Set "mysql_password" in slimpanel.json')
        )
    else:
        checks.append(_check("MySQL root password", True, "A MySQL password is configured", "high"))

    world_writable = []
    for site in session.exec(select(Site)).all():
        root = Path(site.root)
        if not root.is_dir():
            continue
        try:
            mode = stat.S_IMODE(root.stat().st_mode)
        except OSError:
            continue
        if mode & 0o002:
            world_writable.append(f"{site.name} ({oct(mode)[2:]})")
    checks.append(
        _check(
            "Site directory permissions",
            not world_writable,
            "World-writable: " + ", ".join(world_writable) if world_writable
            else "No world-writable site roots",
            "high",
            "chmod 755 the site root from the Files page",
        )
    )

    failed = sshd.failed_logins(limit=50)
    total_failed = sum(row["attempts"] for row in failed)
    checks.append(
        _check(
            "SSH brute force",
            total_failed < 100,
            f"{total_failed} failed SSH attempts in the current log",
            "medium",
            "Block the worst offenders under Security → IP rules",
        )
    )

    panel_attempts = blocked_addresses(session)
    checks.append(
        _check(
            "Panel login attempts",
            not any(row["blocked"] for row in panel_attempts),
            f"{len(panel_attempts)} addresses tried to log in recently",
            "low",
        )
    )

    score = round(100 * sum(1 for c in checks if c["ok"]) / max(1, len(checks)))
    return {
        "score": score,
        "passed": sum(1 for c in checks if c["ok"]),
        "total": len(checks),
        "checks": checks,
    }


def scan_site(session: Session, site_id: int, limit: int = 4000) -> dict:
    """Grep a site for the shapes web shells take. Not a virus scanner."""
    site = session.get(Site, site_id)
    if not site:
        from app.errors import NotFound

        raise NotFound("Site not found")

    root = Path(site.root)
    findings: list[dict] = []
    scanned = 0
    if root.is_dir():
        for path in root.rglob("*"):
            if scanned >= limit:
                break
            if not path.is_file() or path.is_symlink():
                continue
            if path.suffix.lower() not in {".php", ".phtml", ".php5", ".inc"}:
                continue
            scanned += 1
            try:
                if path.stat().st_size > 2 * 1024 * 1024:
                    continue
                blob = path.read_bytes()
            except OSError:
                continue
            match = SUSPICIOUS_PHP.search(blob)
            if match:
                findings.append(
                    {
                        "path": str(path),
                        "pattern": match.group(0).decode(errors="replace")[:120],
                        "size": len(blob),
                        "modified": path.stat().st_mtime,
                    }
                )

    return {
        "site": site.name,
        "root": str(root),
        "scanned": scanned,
        "truncated": scanned >= limit,
        "findings": findings,
    }


def recent_panel_logins(session: Session, limit: int = 100) -> list[LoginLog]:
    return list(session.exec(select(LoginLog).order_by(LoginLog.id.desc()).limit(limit)).all())


def ssh_overview() -> dict:
    return {
        "history": sshd.login_history(limit=50),
        "failed": sshd.failed_logins(limit=50),
        "sessions": _active_sessions(),
    }


def _active_sessions() -> list[dict]:
    result = shell.run(["who"], timeout=15)
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            rows.append(
                {
                    "user": parts[0],
                    "tty": parts[1],
                    "since": " ".join(parts[2:4]) if len(parts) > 3 else "",
                    "from": parts[-1].strip("()") if parts[-1].startswith("(") else "",
                }
            )
    return rows


def kernel_hardening() -> list[dict]:
    """A few sysctl values worth flagging on a public host."""
    wanted = {
        "net.ipv4.tcp_syncookies": "1",
        "net.ipv4.conf.all.accept_redirects": "0",
        "net.ipv4.conf.all.accept_source_route": "0",
        "net.ipv4.conf.all.rp_filter": "1",
        "net.ipv4.icmp_echo_ignore_broadcasts": "1",
        "kernel.randomize_va_space": "2",
    }
    rows = []
    for key, expected in wanted.items():
        result = shell.run(["sysctl", "-n", key], timeout=10)
        current = result.stdout.strip()
        rows.append({"key": key, "current": current, "expected": expected, "ok": current == expected})
    return rows


def panel_file_permissions() -> list[dict]:
    """The panel's own secrets should not be readable by everyone."""
    rows = []
    for path in (
        settings.data_dir / "secret.key",
        settings.data_dir / "slimpanel.db",
        Path(os.environ.get("SLIMPANEL_CONFIG", "")) if os.environ.get("SLIMPANEL_CONFIG") else None,
    ):
        if path is None or not path.exists():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        rows.append(
            {
                "path": str(path),
                "mode": oct(mode)[2:].zfill(3),
                "ok": not mode & 0o077,
            }
        )
    return rows
