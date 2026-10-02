from __future__ import annotations

import re
from pathlib import Path

from app.config import settings
from app.errors import NotFound, PanelError
from app.services import shell

VERSION_IN_PATH = re.compile(r"(\d)\.?(\d)")
INI_LINE = re.compile(r"^\s*([A-Za-z0-9_.]+)\s*=\s*(.*?)\s*$")

# The handful of php.ini keys a panel is actually asked about.
TUNABLE_KEYS = [
    "memory_limit",
    "max_execution_time",
    "max_input_time",
    "post_max_size",
    "upload_max_filesize",
    "max_file_uploads",
    "default_socket_timeout",
    "date.timezone",
    "display_errors",
    "error_reporting",
    "short_open_tag",
    "expose_php",
    "disable_functions",
    "opcache.enable",
    "opcache.memory_consumption",
    "opcache.max_accelerated_files",
]


def _normalise(raw: str) -> str:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) >= 2:
        return f"{digits[0]}.{digits[1]}"
    return raw


def _candidate_dirs() -> list[Path]:
    dirs: list[Path] = []
    for root in settings.php_roots:
        base = Path(root)
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if child.is_dir():
                dirs.append(child)
    return dirs


def discover() -> list[dict]:
    """Find every PHP build on the box: aaPanel layout, distro layout, or $PATH."""
    found: dict[str, dict] = {}

    for directory in _candidate_dirs():
        label = directory.name
        if not any(ch.isdigit() for ch in label):
            continue
        version = _normalise(label)
        binary = None
        for guess in (directory / "bin" / "php", directory / "php"):
            if guess.is_file():
                binary = guess
                break
        ini = None
        for guess in (
            directory / "etc" / "php.ini",
            directory / "lib" / "php.ini",
            directory / "php.ini",
            directory / "cli" / "php.ini",
            directory / "fpm" / "php.ini",
        ):
            if guess.is_file():
                ini = guess
                break
        fpm_conf = None
        for guess in (
            directory / "etc" / "php-fpm.conf",
            directory / "fpm" / "php-fpm.conf",
            directory / "fpm" / "pool.d" / "www.conf",
            directory / "etc" / "php-fpm.d" / "www.conf",
        ):
            if guess.is_file():
                fpm_conf = guess
                break
        found[version] = {
            "version": version,
            "label": f"PHP {version}",
            "path": str(directory),
            "binary": str(binary) if binary else "",
            "ini": str(ini) if ini else "",
            "fpm_conf": str(fpm_conf) if fpm_conf else "",
        }

    result = shell.run(["php", "-v"], timeout=10)
    match = re.search(r"PHP (\d+)\.(\d+)", result.stdout)
    if match:
        version = f"{match.group(1)}.{match.group(2)}"
        found.setdefault(
            version,
            {
                "version": version,
                "label": f"PHP {version}",
                "path": "",
                "binary": "php",
                "ini": _ini_from_binary("php"),
                "fpm_conf": "",
            },
        )

    for item in found.values():
        # An aaPanel box can hold a half-finished build (just src/), so say so
        # rather than offering to configure a PHP that has no binary.
        item["installed"] = bool(item["binary"] or item["ini"])
        item["service"] = fpm_service(item["version"])
        item["running"] = _service_active(item["service"])
        item["socket"] = settings.php_fpm_socket.format(version=item["version"])
    return sorted(found.values(), key=lambda row: row["version"])


def _ini_from_binary(binary: str) -> str:
    result = shell.run([binary, "--ini"], timeout=10)
    for line in result.output.splitlines():
        if "Loaded Configuration File" in line and "=>" in line:
            value = line.split("=>", 1)[1].strip()
            return "" if value in {"(none)", ""} else value
    return ""


def fpm_service(version: str) -> str:
    compact = version.replace(".", "")
    for name in (f"php{version}-fpm", f"php-fpm-{version}", f"php-fpm{compact}", f"php-fpm-{compact}"):
        if shell.run([settings.systemctl_bin, "cat", name], timeout=10).ok:
            return name
    return f"php{version}-fpm"


def _service_active(service: str) -> bool:
    return shell.run([settings.systemctl_bin, "is-active", service], timeout=10).stdout.strip() == "active"


def get(version: str) -> dict:
    for item in discover():
        if item["version"] == version:
            return item
    raise NotFound(f"PHP {version} is not installed")


def read_ini(version: str) -> dict:
    info = get(version)
    if not info["ini"]:
        raise NotFound(f"No php.ini found for PHP {version}")
    text = Path(info["ini"]).read_text(errors="replace")
    values = {}
    for line in text.splitlines():
        if line.lstrip().startswith((";", "#")):
            continue
        match = INI_LINE.match(line)
        if match and match.group(1) in TUNABLE_KEYS:
            values[match.group(1)] = match.group(2)
    return {"path": info["ini"], "content": text, "values": values, "tunable": TUNABLE_KEYS}


def write_ini(version: str, content: str) -> dict:
    info = get(version)
    path = Path(info["ini"])
    if not path.is_file():
        raise NotFound(f"No php.ini found for PHP {version}")
    backup = path.with_suffix(path.suffix + ".slimpanel.bak")
    backup.write_text(path.read_text(errors="replace"))
    path.write_text(content)
    return {"path": str(path), "backup": str(backup)}


def set_values(version: str, values: dict[str, str]) -> dict:
    """Patch individual php.ini keys, keeping comments and ordering intact."""
    info = get(version)
    path = Path(info["ini"])
    if not path.is_file():
        raise NotFound(f"No php.ini found for PHP {version}")

    for key in values:
        if key not in TUNABLE_KEYS:
            raise PanelError(f"{key} is not an editable php.ini key")

    lines = path.read_text(errors="replace").splitlines()
    remaining = dict(values)
    for index, line in enumerate(lines):
        match = INI_LINE.match(line)
        if not match or line.lstrip().startswith((";", "#")):
            continue
        key = match.group(1)
        if key in remaining:
            lines[index] = f"{key} = {remaining.pop(key)}"
    for key, value in remaining.items():
        lines.append(f"{key} = {value}")

    backup = path.with_suffix(path.suffix + ".slimpanel.bak")
    backup.write_text(path.read_text(errors="replace"))
    path.write_text("\n".join(lines) + "\n")
    return read_ini(version)


def extensions(version: str) -> list[dict]:
    info = get(version)
    binary = info["binary"] or "php"
    result = shell.run([binary, "-m"], timeout=20)
    loaded = {line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith("[")}

    available = []
    ext_dir = Path(info["path"]) / "lib" / "php" / "extensions" if info["path"] else None
    if ext_dir and ext_dir.is_dir():
        for child in ext_dir.rglob("*.so"):
            available.append(child.stem)

    names = sorted(loaded | set(available))
    return [{"name": name, "loaded": name in loaded} for name in names]


def fpm_status(version: str) -> dict:
    info = get(version)
    service = info["service"]
    status = shell.run([settings.systemctl_bin, "status", service, "--no-pager"], timeout=15)
    return {
        "version": version,
        "service": service,
        "running": info["running"],
        "socket": info["socket"],
        "status": status.output[:4000],
    }


def service_action(version: str, action: str) -> shell.Result:
    if action not in {"start", "stop", "restart", "reload"}:
        raise PanelError(f"Unsupported action '{action}'")
    info = get(version)
    return shell.run([settings.systemctl_bin, action, info["service"]], timeout=60)


def read_fpm_conf(version: str) -> dict:
    info = get(version)
    if not info["fpm_conf"]:
        raise NotFound(f"No php-fpm config found for PHP {version}")
    path = Path(info["fpm_conf"])
    return {"path": str(path), "content": path.read_text(errors="replace")}


def write_fpm_conf(version: str, content: str) -> dict:
    info = get(version)
    if not info["fpm_conf"]:
        raise NotFound(f"No php-fpm config found for PHP {version}")
    path = Path(info["fpm_conf"])
    path.with_suffix(path.suffix + ".slimpanel.bak").write_text(path.read_text(errors="replace"))
    path.write_text(content)
    return {"path": str(path)}


def slow_log(version: str, lines: int = 200) -> dict:
    info = get(version)
    candidates = [
        Path(info["path"]) / "var" / "log" / "slow.log" if info["path"] else None,
        Path(f"/var/log/php{version}-fpm.log"),
        Path(f"/www/server/php/{version.replace('.', '')}/var/log/slow.log"),
    ]
    for path in candidates:
        if path and path.is_file():
            body = path.read_text(errors="replace").splitlines()[-lines:]
            return {"path": str(path), "lines": body}
    return {"path": "", "lines": []}
