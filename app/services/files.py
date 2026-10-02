from __future__ import annotations

import os
import pwd
import grp
import shutil
import stat
import zipfile
from datetime import datetime
from pathlib import Path

from app.errors import Conflict, NotFound, PanelError, UnsafePath
from app.services.paths import allowed_roots, resolve_for_create, resolve_managed

TEXT_LIMIT = 4 * 1024 * 1024


def _owner(path_stat: os.stat_result) -> tuple[str, str]:
    try:
        user = pwd.getpwuid(path_stat.st_uid).pw_name
    except KeyError:
        user = str(path_stat.st_uid)
    try:
        group = grp.getgrgid(path_stat.st_gid).gr_name
    except KeyError:
        group = str(path_stat.st_gid)
    return user, group


def describe(path: Path) -> dict:
    info = path.lstat()
    user, group = _owner(info)
    return {
        "name": path.name,
        "path": str(path),
        "is_dir": stat.S_ISDIR(info.st_mode),
        "is_link": stat.S_ISLNK(info.st_mode),
        "size": info.st_size,
        "mode": oct(stat.S_IMODE(info.st_mode))[2:].zfill(3),
        "owner": user,
        "group": group,
        "modified": datetime.fromtimestamp(info.st_mtime).isoformat(timespec="seconds"),
    }


def roots() -> list[str]:
    return [str(root) for root in allowed_roots()]


def list_dir(raw_path: str) -> dict:
    path = resolve_managed(raw_path)
    if not path.is_dir():
        raise NotFound("Directory not found")

    entries = []
    for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        try:
            entries.append(describe(child))
        except OSError:
            continue
    return {"path": str(path), "parent": str(path.parent), "entries": entries}


def read_file(raw_path: str) -> dict:
    path = resolve_managed(raw_path)
    if not path.is_file():
        raise NotFound("File not found")
    if path.stat().st_size > TEXT_LIMIT:
        raise PanelError("File is too large to edit in the panel")
    try:
        content = path.read_text()
    except UnicodeDecodeError as exc:
        raise PanelError("File is not valid UTF-8 text") from exc
    return {"path": str(path), "content": content}


def write_file(raw_path: str, content: str) -> dict:
    path = resolve_for_create(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return describe(path)


def create_dir(raw_path: str) -> dict:
    path = resolve_for_create(raw_path)
    if path.exists():
        raise Conflict("Path already exists")
    path.mkdir(parents=True)
    return describe(path)


def delete(raw_path: str) -> None:
    path = resolve_managed(raw_path)
    if path in allowed_roots():
        raise UnsafePath("Refusing to delete a managed root")
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def move(raw_source: str, raw_target: str) -> dict:
    source = resolve_managed(raw_source)
    target = resolve_for_create(raw_target)
    if source in allowed_roots():
        raise UnsafePath("Refusing to move a managed root")
    if target.exists():
        raise Conflict("Target already exists")
    shutil.move(str(source), str(target))
    return describe(target)


def copy(raw_source: str, raw_target: str) -> dict:
    source = resolve_managed(raw_source)
    target = resolve_for_create(raw_target)
    if target.exists():
        raise Conflict("Target already exists")
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)
    return describe(target)


def chmod(raw_path: str, mode: str, recursive: bool = False) -> dict:
    path = resolve_managed(raw_path)
    try:
        bits = int(mode, 8)
    except ValueError as exc:
        raise PanelError("Mode must be octal, for example 755") from exc
    if not 0 <= bits <= 0o777:
        raise PanelError("Mode out of range")

    path.chmod(bits)
    if recursive and path.is_dir():
        for child in path.rglob("*"):
            try:
                child.chmod(bits)
            except OSError:
                continue
    return describe(path)


def compress(raw_paths: list[str], raw_target: str) -> dict:
    target = resolve_for_create(raw_target)
    if target.exists():
        raise Conflict("Archive already exists")

    sources = [resolve_managed(item) for item in raw_paths]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for source in sources:
            if source.is_dir():
                for child in source.rglob("*"):
                    if child.is_file():
                        archive.write(child, child.relative_to(source.parent))
            else:
                archive.write(source, source.name)
    return describe(target)


def extract(raw_archive: str, raw_target: str) -> dict:
    archive_path = resolve_managed(raw_archive)
    target = resolve_managed(raw_target) if Path(raw_target).exists() else resolve_for_create(raw_target)
    target.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.namelist():
            destination = (target / member).resolve()
            if not str(destination).startswith(str(target.resolve())):
                raise UnsafePath(f"Archive entry escapes the target directory: {member}")
        archive.extractall(target)
    return describe(target)


def save_upload(raw_dir: str, filename: str, data: bytes) -> dict:
    if "/" in filename or filename in {"", ".", ".."}:
        raise UnsafePath("Invalid upload filename")
    directory = resolve_managed(raw_dir)
    if not directory.is_dir():
        raise NotFound("Upload directory not found")
    target = directory / filename
    target.write_bytes(data)
    return describe(target)


def resolve_download(raw_path: str) -> Path:
    path = resolve_managed(raw_path)
    if not path.is_file():
        raise NotFound("File not found")
    return path


def tail(raw_path: str, lines: int = 200) -> dict:
    path = resolve_managed(raw_path)
    if not path.is_file():
        raise NotFound("File not found")

    block = 8192
    size = path.stat().st_size
    collected: list[bytes] = []
    with path.open("rb") as handle:
        remaining = size
        while remaining > 0 and sum(chunk.count(b"\n") for chunk in collected) <= lines:
            step = min(block, remaining)
            remaining -= step
            handle.seek(remaining)
            collected.insert(0, handle.read(step))
    text = b"".join(collected).decode("utf-8", errors="replace")
    return {"path": str(path), "lines": text.splitlines()[-lines:]}
