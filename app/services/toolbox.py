from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

import psutil

from app.config import settings
from app.errors import PanelError
from app.services import shell

SYSCTL_FILE = Path("/etc/sysctl.d/99-slimpanel.conf")
HOSTNAME_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9.-]{0,61}[a-zA-Z0-9])?$")

# The kernel knobs aaPanel's toolbox exposes for a busy web server.
TUNABLE_SYSCTL = [
    "net.ipv4.tcp_fin_timeout",
    "net.ipv4.tcp_tw_reuse",
    "net.ipv4.tcp_max_syn_backlog",
    "net.ipv4.ip_local_port_range",
    "net.core.somaxconn",
    "net.core.netdev_max_backlog",
    "net.ipv4.tcp_syncookies",
    "net.ipv4.tcp_keepalive_time",
    "vm.swappiness",
    "vm.overcommit_memory",
    "fs.file-max",
]


def info() -> dict:
    return {
        "hostname": shell.run(["hostname"], timeout=10).stdout.strip() or os.uname().nodename,
        "timezone": timezone(),
        "kernel": os.uname().release,
        "arch": os.uname().machine,
        "swap": swap_info(),
        "dns": dns_servers(),
        "package_manager": _package_manager(),
    }


def _package_manager() -> str:
    from app.services.apps import package_manager

    return package_manager()


def timezone() -> str:
    result = shell.run(["timedatectl", "show", "-p", "Timezone", "--value"], timeout=10)
    if result.ok and result.stdout.strip():
        return result.stdout.strip()
    link = Path("/etc/localtime")
    if link.is_symlink():
        target = str(link.resolve())
        if "zoneinfo/" in target:
            return target.split("zoneinfo/", 1)[1]
    return ""


def timezones() -> list[str]:
    result = shell.run(["timedatectl", "list-timezones"], timeout=20)
    if result.ok and result.stdout.strip():
        return result.stdout.split()
    base = Path("/usr/share/zoneinfo")
    if not base.is_dir():
        return []
    skip = {"posix", "right", "SystemV"}
    names = []
    for path in base.rglob("*"):
        if path.is_file() and not path.name.endswith(".tab") and path.parts[4:5] != tuple(skip):
            names.append(str(path.relative_to(base)))
    return sorted(names)


TIMEZONE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_+-]*(?:/[A-Za-z0-9_+-]+)*$")


def set_timezone(name: str) -> shell.Result:
    cleaned = name.strip()
    # The name indexes into /usr/share/zoneinfo, so ".." and absolute paths are out.
    if not TIMEZONE_PATTERN.match(cleaned) or ".." in cleaned:
        raise PanelError("Pick a timezone like Asia/Ho_Chi_Minh")
    if "/" not in cleaned and cleaned not in {"UTC", "GMT", "Zulu", "Universal"}:
        raise PanelError("Pick a timezone like Asia/Ho_Chi_Minh")
    if not Path("/usr/share/zoneinfo", cleaned).is_file() and not settings.dry_run:
        raise PanelError(f"Unknown timezone: {name}")
    name = cleaned
    result = shell.run(["timedatectl", "set-timezone", name], timeout=20)
    if not result.ok:
        raise PanelError("Could not set the timezone", result.output)
    return result


def set_hostname(name: str) -> shell.Result:
    cleaned = name.strip()
    if not HOSTNAME_PATTERN.match(cleaned):
        raise PanelError("That is not a valid hostname")
    result = shell.run(["hostnamectl", "set-hostname", cleaned], timeout=20)
    if not result.ok:
        result = shell.run(["hostname", cleaned], timeout=20)
    if not result.ok:
        raise PanelError("Could not set the hostname", result.output)
    return result


def dns_servers() -> list[str]:
    servers = []
    path = Path("/etc/resolv.conf")
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines():
            if line.strip().startswith("nameserver"):
                parts = line.split()
                if len(parts) > 1:
                    servers.append(parts[1])
    return servers


def set_dns(servers: list[str]) -> dict:
    import ipaddress

    cleaned = []
    for server in servers:
        value = server.strip()
        if not value:
            continue
        try:
            ipaddress.ip_address(value)
        except ValueError as exc:
            raise PanelError(f"'{value}' is not an IP address") from exc
        cleaned.append(value)
    if not cleaned:
        raise PanelError("At least one nameserver is required")

    path = Path("/etc/resolv.conf")
    if path.is_symlink():
        raise PanelError(
            "/etc/resolv.conf is managed by systemd-resolved or NetworkManager; "
            "change DNS there instead of overwriting the symlink"
        )
    if not settings.dry_run:
        body = "# Managed by SlimPanel\n" + "".join(f"nameserver {s}\n" for s in cleaned)
        path.write_text(body)
    return {"servers": cleaned}


def resolve_test(host: str) -> dict:
    cleaned = host.strip()
    if not cleaned or any(ch in cleaned for ch in " ;|&$`\n"):
        raise PanelError("Invalid hostname")
    tool = "dig" if shutil.which("dig") else ("host" if shutil.which("host") else "getent")
    argv = {
        "dig": ["dig", "+short", cleaned],
        "host": ["host", cleaned],
        "getent": ["getent", "hosts", cleaned],
    }[tool]
    result = shell.run(argv, timeout=20)
    return {"tool": tool, "output": result.output[:4000], "ok": result.ok}


def swap_info() -> dict:
    swap = psutil.swap_memory()
    files = []
    path = Path("/proc/swaps")
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3:
                files.append({"name": parts[0], "type": parts[1], "size_kb": int(parts[2])})
    return {"total": swap.total, "used": swap.used, "percent": swap.percent, "entries": files}


def create_swap(size_mb: int, path: str = "/swapfile") -> dict:
    if not 64 <= size_mb <= 65536:
        raise PanelError("Swap size must be between 64MB and 64GB")
    target = Path(path)
    if target.exists() and not settings.dry_run:
        raise PanelError(f"{target} already exists; remove it first")

    free = shutil.disk_usage(str(target.parent)).free
    if free < size_mb * 1024 * 1024 * 1.1 and not settings.dry_run:
        raise PanelError("Not enough free disk space for that swap file")

    steps = [
        f"fallocate -l {size_mb}M {target} || dd if=/dev/zero of={target} bs=1M count={size_mb}",
        f"chmod 600 {target}",
        f"mkswap {target}",
        f"swapon {target}",
    ]
    outputs = []
    for step in steps:
        result = shell.run(f"/bin/bash -lc {step!r}", timeout=600)
        outputs.append(result.output)
        if not result.ok:
            raise PanelError("Creating the swap file failed", "\n".join(outputs))

    if not settings.dry_run:
        fstab = Path("/etc/fstab")
        line = f"{target} none swap sw 0 0\n"
        body = fstab.read_text(errors="replace") if fstab.is_file() else ""
        if str(target) not in body:
            fstab.write_text(body.rstrip("\n") + "\n" + line)
    return {"path": str(target), "size_mb": size_mb, "output": "\n".join(outputs)[:4000]}


def remove_swap(path: str = "/swapfile") -> dict:
    target = Path(path)
    shell.run(["swapoff", str(target)], timeout=120)
    if not settings.dry_run:
        target.unlink(missing_ok=True)
        fstab = Path("/etc/fstab")
        if fstab.is_file():
            lines = [l for l in fstab.read_text(errors="replace").splitlines() if str(target) not in l]
            fstab.write_text("\n".join(lines) + "\n")
    return {"path": str(target), "removed": True}


def release_memory() -> dict:
    """Drop page cache and reclaim what the kernel will give back."""
    before = psutil.virtual_memory().available
    shell.run("sync", timeout=60)
    if not settings.dry_run:
        try:
            Path("/proc/sys/vm/drop_caches").write_text("3\n")
        except OSError as exc:
            raise PanelError(f"Could not drop caches: {exc}") from exc
    after = psutil.virtual_memory().available
    return {"before": before, "after": after, "freed": max(0, after - before)}


def sysctl_values() -> list[dict]:
    rows = []
    for key in TUNABLE_SYSCTL:
        result = shell.run(["sysctl", "-n", key], timeout=10)
        rows.append({"key": key, "value": result.stdout.strip() if result.ok else ""})
    return rows


def set_sysctl(values: dict[str, str]) -> list[dict]:
    for key in values:
        if key not in TUNABLE_SYSCTL:
            raise PanelError(f"{key} is not an editable kernel parameter")

    for key, value in values.items():
        cleaned = str(value).strip()
        if not re.fullmatch(r"[\d\s]+", cleaned):
            raise PanelError(f"{key} must be numeric")
        result = shell.run(["sysctl", "-w", f"{key}={cleaned}"], timeout=10)
        if not result.ok:
            raise PanelError(f"Could not set {key}", result.output)

    if not settings.dry_run:
        kept = []
        if SYSCTL_FILE.is_file():
            kept = [
                line
                for line in SYSCTL_FILE.read_text(errors="replace").splitlines()
                if line.split("=")[0].strip() not in values
            ]
        kept += [f"{key} = {str(value).strip()}" for key, value in values.items()]
        SYSCTL_FILE.parent.mkdir(parents=True, exist_ok=True)
        SYSCTL_FILE.write_text("\n".join(kept) + "\n")
    return sysctl_values()


def ports_in_use() -> list[dict]:
    from app.services.firewall import listening_ports

    return listening_ports()


def reboot() -> shell.Result:
    return shell.run([settings.systemctl_bin, "reboot"], timeout=20)
