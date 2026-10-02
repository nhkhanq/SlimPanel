from __future__ import annotations

import fnmatch
import os
import pwd
import grp
import shutil
import stat
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.errors import Conflict, NotFound, PanelError, UnsafePath
from app.services.paths import allowed_roots, resolve_for_create, resolve_managed

TEXT_LIMIT = 4 * 1024 * 1024
ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")

# Extensions the editor offers syntax highlighting for, so the UI knows the mode.
EDITOR_MODES = {
    ".conf": "nginx", ".nginx": "nginx", ".php": "php", ".py": "python",
    ".js": "javascript", ".mjs": "javascript", ".ts": "typescript", ".json": "json",
    ".html": "html", ".htm": "html", ".vue": "html", ".css": "css", ".scss": "css",
    ".sh": "shell", ".bash": "shell", ".sql": "sql", ".yml": "yaml", ".yaml": "yaml",
    ".xml": "xml", ".md": "markdown", ".ini": "ini", ".env": "ini", ".toml": "ini",
    ".go": "go", ".java": "java", ".rb": "ruby", ".rs": "rust", ".c": "c", ".cpp": "cpp",
}


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


def delete(raw_path: str, session=None, force: bool = False) -> dict:
    """Bin the path when the recycle bin is on, otherwise remove it outright."""
    path = resolve_managed(raw_path)
    if path in allowed_roots():
        raise UnsafePath("Refusing to delete a managed root")
    if not path.exists() and not path.is_symlink():
        raise NotFound(f"{path} does not exist")

    if session is not None and settings.recycle_bin and not force:
        from app.services import recycle

        item = recycle.move_to_bin(session, str(path))
        return {"path": str(path), "recycled": True, "recycle_id": item.id}

    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
    return {"path": str(path), "recycled": False}


def delete_many(raw_paths: list[str], session=None, force: bool = False) -> list[dict]:
    """Delete each path independently: one bad entry must not abort the batch."""
    results = []
    for raw in raw_paths:
        try:
            results.append({"ok": True, **delete(raw, session=session, force=force)})
        except PanelError as exc:
            results.append({"ok": False, "path": raw, "error": exc.message})
        except OSError as exc:
            results.append({"ok": False, "path": raw, "error": str(exc)})
    return results


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


def _tar_mode(name: str) -> str | None:
    lowered = name.lower()
    if lowered.endswith((".tar.gz", ".tgz")):
        return "w:gz"
    if lowered.endswith((".tar.bz2", ".tbz2")):
        return "w:bz2"
    if lowered.endswith((".tar.xz", ".txz")):
        return "w:xz"
    if lowered.endswith(".tar"):
        return "w"
    return None


def compress(raw_paths: list[str], raw_target: str) -> dict:
    """Zip or tar, chosen from the target's suffix."""
    target = resolve_for_create(raw_target)
    if target.exists():
        raise Conflict("Archive already exists")
    if not target.name.lower().endswith(ARCHIVE_SUFFIXES):
        raise PanelError(f"Archive name must end in one of: {', '.join(ARCHIVE_SUFFIXES)}")

    sources = [resolve_managed(item) for item in raw_paths]
    if not sources:
        raise PanelError("Select something to compress")

    mode = _tar_mode(target.name)
    if mode:
        with tarfile.open(target, mode) as archive:
            for source in sources:
                archive.add(source, arcname=source.name)
    else:
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
    root = target.resolve()

    def guard(member_name: str) -> None:
        destination = (target / member_name).resolve()
        if destination != root and root not in destination.parents:
            raise UnsafePath(f"Archive entry escapes the target directory: {member_name}")

    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.namelist():
                guard(member)
            archive.extractall(target)
    elif tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path) as archive:
            for member in archive.getmembers():
                if member.islnk() or member.issym():
                    raise UnsafePath(f"Refusing to extract a link: {member.name}")
                guard(member.name)
            archive.extractall(target)
    else:
        raise PanelError("That file is not a zip or tar archive")
    return describe(target)


def archive_contents(raw_archive: str, limit: int = 500) -> dict:
    """Peek inside an archive before unpacking it."""
    archive_path = resolve_managed(raw_archive)
    entries: list[dict] = []
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist()[:limit]:
                entries.append({"name": info.filename, "size": info.file_size,
                                "is_dir": info.is_dir()})
        total = len(zipfile.ZipFile(archive_path).infolist())
    elif tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path) as archive:
            members = archive.getmembers()
            total = len(members)
            for member in members[:limit]:
                entries.append({"name": member.name, "size": member.size,
                                "is_dir": member.isdir()})
    else:
        raise PanelError("That file is not a zip or tar archive")
    return {"path": str(archive_path), "entries": entries, "total": total,
            "truncated": total > limit}


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


def chown(raw_path: str, owner: str, group: str = "", recursive: bool = False) -> dict:
    """Change ownership, by name or numeric id."""
    path = resolve_managed(raw_path)

    def resolve_uid(value: str) -> int:
        if value.isdigit():
            return int(value)
        try:
            return pwd.getpwnam(value).pw_uid
        except KeyError as exc:
            raise PanelError(f"No such user: {value}") from exc

    def resolve_gid(value: str) -> int:
        if value.isdigit():
            return int(value)
        try:
            return grp.getgrnam(value).gr_gid
        except KeyError as exc:
            raise PanelError(f"No such group: {value}") from exc

    uid = resolve_uid(owner) if owner else -1
    gid = resolve_gid(group) if group else -1

    os.chown(path, uid, gid)
    if recursive and path.is_dir():
        for child in path.rglob("*"):
            try:
                os.chown(child, uid, gid)
            except OSError:
                continue
    return describe(path)


def search(
    raw_root: str,
    pattern: str = "",
    contains: str = "",
    max_results: int = 300,
    max_files: int = 60000,
) -> dict:
    """Find files by name glob and, optionally, by content."""
    root = resolve_managed(raw_root)
    if not root.is_dir():
        raise NotFound("Directory not found")
    if not pattern and not contains:
        raise PanelError("Give a filename pattern, a content string, or both")

    glob = pattern.strip() or "*"
    needle = contains.encode() if contains else b""
    matches: list[dict] = []
    visited = 0

    for path in root.rglob("*"):
        if visited >= max_files or len(matches) >= max_results:
            break
        if not path.is_file() or path.is_symlink():
            continue
        visited += 1
        if not fnmatch.fnmatch(path.name, glob):
            continue
        if needle:
            try:
                if path.stat().st_size > 8 * 1024 * 1024:
                    continue
                if needle not in path.read_bytes():
                    continue
            except OSError:
                continue
        try:
            matches.append(describe(path))
        except OSError:
            continue

    return {
        "root": str(root),
        "pattern": glob,
        "contains": contains,
        "scanned": visited,
        "truncated": visited >= max_files or len(matches) >= max_results,
        "matches": matches,
    }


def directory_usage(raw_path: str, depth: int = 1) -> dict:
    """Size of each child, so the UI can show what is filling a disk."""
    path = resolve_managed(raw_path)
    if not path.is_dir():
        raise NotFound("Directory not found")

    def size_of(target: Path) -> tuple[int, int]:
        total = count = 0
        for child in target.rglob("*"):
            try:
                if child.is_file() and not child.is_symlink():
                    total += child.stat().st_size
                    count += 1
            except OSError:
                continue
        return total, count

    rows = []
    for child in sorted(path.iterdir()):
        try:
            if child.is_dir() and not child.is_symlink():
                total, count = size_of(child)
            elif child.is_file():
                total, count = child.stat().st_size, 1
            else:
                continue
        except OSError:
            continue
        rows.append({"name": child.name, "path": str(child), "is_dir": child.is_dir(),
                     "size": total, "files": count})

    rows.sort(key=lambda row: row["size"], reverse=True)
    return {"path": str(path), "total": sum(row["size"] for row in rows), "entries": rows[:200]}


def editor_mode(raw_path: str) -> str:
    name = Path(raw_path).name.lower()
    if name in {"dockerfile", "makefile"}:
        return "shell"
    if name.startswith(".env"):
        return "ini"
    return EDITOR_MODES.get(Path(name).suffix, "text")


def read_file_meta(raw_path: str) -> dict:
    info = read_file(raw_path)
    info["mode"] = editor_mode(raw_path)
    info["stat"] = describe(resolve_managed(raw_path))
    return info


def duplicate(raw_path: str) -> dict:
    """Copy next to the original, the way a file manager's Duplicate works."""
    source = resolve_managed(raw_path)
    stem = source.stem if source.suffix else source.name
    suffix = source.suffix
    for index in range(1, 100):
        candidate = source.with_name(f"{stem}_copy{'' if index == 1 else index}{suffix}")
        if not candidate.exists():
            if source.is_dir():
                shutil.copytree(source, candidate)
            else:
                shutil.copy2(source, candidate)
            return describe(candidate)
    raise Conflict("Too many copies already exist")


def download_remote(raw_dir: str, url: str, filename: str = "") -> dict:
    """Fetch a URL straight onto the server, as a background task."""
    from urllib.parse import urlparse

    import shlex

    from app.services import tasks
    from app.db import engine
    from sqlmodel import Session

    directory = resolve_managed(raw_dir)
    if not directory.is_dir():
        raise NotFound("Directory not found")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise PanelError("Only http:// and https:// downloads are supported")

    name = filename.strip() or Path(parsed.path).name or "download.bin"
    if "/" in name or name in {"", ".", ".."}:
        raise UnsafePath("Invalid download filename")

    target = directory / name
    command = f"curl -fL --retry 2 -o {shlex.quote(str(target))} {shlex.quote(url)}"
    with Session(engine) as session:
        task = tasks.run_shell(session, f"Download {name}", command, timeout=7200)
        return {"task_id": task.id, "target": str(target), "url": url}


def write_many(entries: list[dict]) -> list[dict]:
    results = []
    for entry in entries:
        try:
            results.append({"ok": True, **write_file(entry["path"], entry.get("content", ""))})
        except (PanelError, KeyError) as exc:
            results.append({"ok": False, "path": entry.get("path", ""), "error": str(exc)})
    return results
