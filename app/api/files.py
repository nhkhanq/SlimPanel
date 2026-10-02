from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings
from app.deps import SessionDep, UserDep, audit
from app.schemas import ChmodRequest, FileMove, FileWrite, Ok
from app.services import files

router = APIRouter(prefix="/files", tags=["files"])

MAX_UPLOAD = 2 * 1024 * 1024 * 1024


class ArchiveRequest(BaseModel):
    paths: list[str]
    target: str


class ExtractRequest(BaseModel):
    archive: str
    target: str


class ChownRequest(BaseModel):
    path: str
    owner: str
    group: str = ""
    recursive: bool = False


class SearchRequest(BaseModel):
    root: str
    pattern: str = ""
    contains: str = ""
    max_results: int = 300


class RemoteDownload(BaseModel):
    path: str
    url: str
    filename: str = ""


class PathsRequest(BaseModel):
    paths: list[str]
    force: bool = False


class BatchWrite(BaseModel):
    entries: list[dict]


@router.get("/roots")
def roots(user: UserDep):
    return {
        "roots": files.roots(),
        "www_root": str(settings.www_root),
        "log_root": str(settings.log_root),
        "recycle_bin": settings.recycle_bin,
    }


@router.get("/list")
def list_dir(path: str, user: UserDep):
    return files.list_dir(path)


@router.get("/read")
def read_file(path: str, user: UserDep):
    return files.read_file_meta(path)


@router.get("/tail")
def tail_file(path: str, user: UserDep, lines: int = 200):
    return files.tail(path, min(lines, 5000))


@router.get("/usage")
def usage(path: str, user: UserDep):
    return files.directory_usage(path)


@router.post("/search")
def search(payload: SearchRequest, user: UserDep):
    return files.search(
        payload.root, payload.pattern, payload.contains, min(payload.max_results, 2000)
    )


@router.post("/write")
def write_file(payload: FileWrite, session: SessionDep, user: UserDep):
    info = files.write_file(payload.path, payload.content)
    audit(session, user, "file.write", payload.path)
    return info


@router.post("/write-many")
def write_many(payload: BatchWrite, session: SessionDep, user: UserDep):
    results = files.write_many(payload.entries)
    audit(session, user, "file.write_many", detail=f"{len(results)} files")
    return results


@router.post("/mkdir")
def mkdir(payload: FileWrite, session: SessionDep, user: UserDep):
    info = files.create_dir(payload.path)
    audit(session, user, "file.mkdir", payload.path)
    return info


@router.post("/move")
def move(payload: FileMove, session: SessionDep, user: UserDep):
    info = files.move(payload.source, payload.target)
    audit(session, user, "file.move", f"{payload.source} -> {payload.target}")
    return info


@router.post("/copy")
def copy(payload: FileMove, session: SessionDep, user: UserDep):
    info = files.copy(payload.source, payload.target)
    audit(session, user, "file.copy", f"{payload.source} -> {payload.target}")
    return info


@router.post("/duplicate")
def duplicate(path: str, session: SessionDep, user: UserDep):
    info = files.duplicate(path)
    audit(session, user, "file.duplicate", path)
    return info


@router.post("/chmod")
def chmod(payload: ChmodRequest, session: SessionDep, user: UserDep):
    info = files.chmod(payload.path, payload.mode, payload.recursive)
    audit(session, user, "file.chmod", payload.path, detail=payload.mode)
    return info


@router.post("/chown")
def chown(payload: ChownRequest, session: SessionDep, user: UserDep):
    info = files.chown(payload.path, payload.owner, payload.group, payload.recursive)
    audit(session, user, "file.chown", payload.path, detail=f"{payload.owner}:{payload.group}")
    return info


@router.post("/compress")
def compress(payload: ArchiveRequest, session: SessionDep, user: UserDep):
    info = files.compress(payload.paths, payload.target)
    audit(session, user, "file.compress", payload.target)
    return info


@router.get("/archive")
def archive_contents(path: str, user: UserDep, limit: int = 500):
    return files.archive_contents(path, min(limit, 5000))


@router.post("/extract")
def extract(payload: ExtractRequest, session: SessionDep, user: UserDep):
    info = files.extract(payload.archive, payload.target)
    audit(session, user, "file.extract", payload.archive)
    return info


@router.post("/remote-download")
def remote_download(payload: RemoteDownload, session: SessionDep, user: UserDep):
    info = files.download_remote(payload.path, payload.url, payload.filename)
    audit(session, user, "file.remote_download", payload.url)
    return info


@router.post("/upload")
async def upload(
    session: SessionDep,
    user: UserDep,
    path: str = Form(...),
    upload_file: UploadFile = File(...),
):
    data = await upload_file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        return Ok(ok=False, message="Upload exceeds 2GB")
    info = files.save_upload(path, upload_file.filename or "upload.bin", data)
    audit(session, user, "file.upload", info["path"])
    return info


@router.get("/download")
def download(path: str, user: UserDep):
    target = files.resolve_download(path)
    return FileResponse(target, filename=target.name)


@router.delete("", response_model=Ok)
def delete(path: str, session: SessionDep, user: UserDep, force: bool = False):
    result = files.delete(path, session=session, force=force)
    audit(session, user, "file.delete", path, detail="recycled" if result["recycled"] else "removed")
    return Ok(message="Moved to the recycle bin" if result["recycled"] else "Deleted")


@router.post("/delete-many")
def delete_many(payload: PathsRequest, session: SessionDep, user: UserDep):
    results = files.delete_many(payload.paths, session=session, force=payload.force)
    audit(session, user, "file.delete_many", detail=f"{len(results)} paths")
    return results
