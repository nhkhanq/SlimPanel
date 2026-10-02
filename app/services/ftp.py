from __future__ import annotations

import shutil
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import Conflict, NotFound, PanelError
from app.models import FtpUser
from app.services import shell
from app.services.mysql import generate_password
from app.services.paths import resolve_for_create, resolve_managed

NAME_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")


def backend() -> str:
    """pure-ftpd virtual users, vsftpd, or nothing installed."""
    configured = (settings.ftp_backend or "auto").strip().lower()
    if configured and configured != "auto":
        return configured
    if _pure_pw():
        return "pure-ftpd"
    if shutil.which("vsftpd") or Path("/usr/sbin/vsftpd").is_file():
        return "vsftpd"
    return "none"


# aaPanel ships its own build under /www/server, so $PATH alone is not enough.
_PURE_PW_CANDIDATES = (
    "/www/server/pure-ftpd/bin/pure-pw",
    "/usr/local/pureftpd/bin/pure-pw",
    "/usr/bin/pure-pw",
    "/usr/sbin/pure-pw",
)


def _pure_pw() -> str:
    """Path to pure-pw, or an empty string when pure-ftpd is not installed."""
    configured = (settings.pure_pw_bin or "").strip()
    if configured and Path(configured).is_file():
        return configured
    found = shutil.which(configured) if configured else None
    if found:
        return found
    found = shutil.which("pure-pw")
    if found:
        return found
    for candidate in _PURE_PW_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return ""


def service_name() -> str:
    for name in ("pure-ftpd", "pure-ftpd-mysql", "vsftpd"):
        if shell.run([settings.systemctl_bin, "cat", name], timeout=10).ok:
            return name
    return "pure-ftpd"


def status() -> dict:
    kind = backend()
    service = service_name()
    state = shell.run([settings.systemctl_bin, "is-active", service], timeout=10)
    return {
        "backend": kind,
        "available": kind != "none",
        "service": service,
        "state": state.stdout.strip() or state.stderr.strip() or "unknown",
        "passwd_file": settings.pure_ftpd_passwd,
        "port": 21,
    }


def safe_username(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or len(cleaned) > 32:
        raise PanelError("FTP username must be 1-32 characters")
    if not set(cleaned) <= NAME_ALLOWED:
        raise PanelError("FTP username may contain letters, digits, dot, dash and underscore")
    return cleaned


def list_users(session: Session) -> list[FtpUser]:
    return list(session.exec(select(FtpUser).order_by(FtpUser.username)).all())


def get_user(session: Session, user_id: int) -> FtpUser:
    user = session.get(FtpUser, user_id)
    if not user:
        raise NotFound("FTP user not found")
    return user


def _system_owner() -> tuple[str, str]:
    """The uid/gid pure-ftpd virtual users map onto; www-data where it exists."""
    import grp
    import pwd

    for name in ("www-data", "www", "nginx", "apache", "nobody"):
        try:
            entry = pwd.getpwnam(name)
        except KeyError:
            continue
        try:
            group = grp.getgrgid(entry.pw_gid).gr_name
        except KeyError:
            group = name
        return name, group
    return "nobody", "nogroup"


def _pure_pw_run(args: list[str], stdin: str | None = None) -> shell.Result:
    binary = _pure_pw()
    if not binary and not settings.dry_run:
        raise PanelError("pure-pw was not found; is Pure-FTPd installed?")
    result = shell.run([binary or "pure-pw", *args], stdin=stdin, timeout=60)
    if not result.ok:
        raise PanelError("pure-pw failed", result.output)
    return result


def _commit_pure_pw() -> None:
    passwd = Path(settings.pure_ftpd_passwd)
    binary = _pure_pw()
    if binary and (passwd.is_file() or settings.dry_run):
        shell.run([binary, "mkdb", str(passwd.with_suffix(".pdb")), "-f", str(passwd)], timeout=60)


def create_user(
    session: Session, username: str, password: str = "", home: str = "", quota_mb: int = 0, note: str = ""
) -> FtpUser:
    name = safe_username(username)
    if session.exec(select(FtpUser).where(FtpUser.username == name)).first():
        raise Conflict("That FTP user already exists")

    secret = password or generate_password(16)
    if len(secret) < 8:
        raise PanelError("FTP password must be at least 8 characters")

    raw_home = home.strip() or str(settings.ftp_root / name)
    directory = resolve_for_create(raw_home) if not Path(raw_home).exists() else resolve_managed(raw_home)
    directory.mkdir(parents=True, exist_ok=True)

    kind = backend()
    if kind == "pure-ftpd":
        owner, group = _system_owner()
        args = ["useradd", name, "-u", owner, "-g", group, "-d", str(directory)]
        if quota_mb:
            args += ["-N", str(quota_mb)]
        _pure_pw_run(args, stdin=f"{secret}\n{secret}\n")
        _commit_pure_pw()
        if not settings.dry_run:
            shell.run(["chown", "-R", f"{owner}:{group}", str(directory)], timeout=120)
    elif kind == "none":
        raise PanelError("No FTP server is installed. Install Pure-FTPd from the App Store page.")

    user = FtpUser(
        username=name, password=secret, home=str(directory), quota_mb=quota_mb, note=note
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def set_password(session: Session, user_id: int, password: str = "") -> FtpUser:
    user = get_user(session, user_id)
    secret = password or generate_password(16)
    if len(secret) < 8:
        raise PanelError("FTP password must be at least 8 characters")

    if backend() == "pure-ftpd":
        _pure_pw_run(["passwd", user.username], stdin=f"{secret}\n{secret}\n")
        _commit_pure_pw()

    user.password = secret
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def set_enabled(session: Session, user_id: int, enabled: bool) -> FtpUser:
    user = get_user(session, user_id)
    if backend() == "pure-ftpd":
        # pure-ftpd has no enable flag; a concurrent-session cap of 0 denies login,
        # which is how a virtual user gets switched off in practice.
        _pure_pw_run(["usermod", user.username, "-y", "10" if enabled else "0"])
        _commit_pure_pw()
    user.enabled = enabled
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def set_home(session: Session, user_id: int, home: str) -> FtpUser:
    user = get_user(session, user_id)
    directory = resolve_for_create(home) if not Path(home).exists() else resolve_managed(home)
    directory.mkdir(parents=True, exist_ok=True)
    if backend() == "pure-ftpd":
        _pure_pw_run(["usermod", user.username, "-d", str(directory)])
        _commit_pure_pw()
    user.home = str(directory)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def set_quota(session: Session, user_id: int, quota_mb: int) -> FtpUser:
    user = get_user(session, user_id)
    if quota_mb < 0:
        raise PanelError("Quota cannot be negative")
    if backend() == "pure-ftpd":
        _pure_pw_run(["usermod", user.username, "-N", str(quota_mb)])
        _commit_pure_pw()
    user.quota_mb = quota_mb
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: int, remove_files: bool = False) -> None:
    user = get_user(session, user_id)
    if backend() == "pure-ftpd":
        shell.run([_pure_pw() or "pure-pw", "userdel", user.username], timeout=60)
        _commit_pure_pw()

    home = Path(user.home)
    session.delete(user)
    session.commit()

    if remove_files and home.is_dir() and home != settings.ftp_root:
        try:
            resolve_managed(str(home))
        except PanelError:
            return
        shutil.rmtree(home, ignore_errors=True)


def service_action(action: str) -> shell.Result:
    if action not in {"start", "stop", "restart", "reload"}:
        raise PanelError(f"Unsupported action '{action}'")
    return shell.run([settings.systemctl_bin, action, service_name()], timeout=60)


def logs(lines: int = 200) -> dict:
    for candidate in ("/var/log/pure-ftpd/transfer.log", "/www/wwwlogs/pureftpd.log", "/var/log/vsftpd.log"):
        path = Path(candidate)
        if path.is_file():
            try:
                body = path.read_text(errors="replace").splitlines()[-lines:]
            except OSError:
                continue
            return {"path": str(path), "lines": body}
    return {"path": "", "lines": []}
