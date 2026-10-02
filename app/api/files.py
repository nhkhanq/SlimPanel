from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.schemas import ChmodRequest, FileMove, FileWrite, Ok
from app.services import files

router = APIRouter(prefix="/files", tags=["files"])

MAX_UPLOAD = 200 * 1024 * 1024


class ArchiveRequest(BaseModel):
    paths: list[str]
    target: str


class ExtractRequest(BaseModel):
    archive: str
    target: str


@router.get("/roots")
def roots(user: UserDep):
    return {"roots": files.roots()}


@router.get("/list")
def list_dir(path: str, user: UserDep):
    return files.list_dir(path)


@router.get("/read")
def read_file(path: str, user: UserDep):
    return files.read_file(path)


@router.get("/tail")
def tail_file(path: str, user: UserDep, lines: int = 200):
    return files.tail(path, min(lines, 2000))


@router.post("/write")
def write_file(payload: FileWrite, session: SessionDep, user: UserDep):
    info = files.write_file(payload.path, payload.content)
    audit(session, user, "file.write", payload.path)
    return info


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


@router.post("/chmod")
def chmod(payload: ChmodRequest, session: SessionDep, user: UserDep):
    info = files.chmod(payload.path, payload.mode, payload.recursive)
    audit(session, user, "file.chmod", payload.path, detail=payload.mode)
    return info


@router.post("/compress")
def compress(payload: ArchiveRequest, session: SessionDep, user: UserDep):
    info = files.compress(payload.paths, payload.target)
    audit(session, user, "file.compress", payload.target)
    return info


@router.post("/extract")
def extract(payload: ExtractRequest, session: SessionDep, user: UserDep):
    info = files.extract(payload.archive, payload.target)
    audit(session, user, "file.extract", payload.archive)
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
        return Ok(ok=False, message="Upload exceeds 200MB")
    info = files.save_upload(path, upload_file.filename or "upload.bin", data)
    audit(session, user, "file.upload", info["path"])
    return info


@router.get("/download")
def download(path: str, user: UserDep):
    target = files.resolve_download(path)
    return FileResponse(target, filename=target.name)


@router.delete("", response_model=Ok)
def delete(path: str, session: SessionDep, user: UserDep):
    files.delete(path)
    audit(session, user, "file.delete", path)
    return Ok(message="Deleted")
