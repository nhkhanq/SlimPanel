from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from app.deps import SessionDep, UserDep, audit
from app.models import Database
from app.schemas import DatabaseCreate, DatabaseOut, Ok
from app.services import mysql

router = APIRouter(prefix="/databases", tags=["databases"])


class ResetPassword(BaseModel):
    password: str = ""


class ImportRequest(BaseModel):
    sql_file: str


@router.get("/status")
def server_status(user: UserDep):
    return {"available": mysql.server_available(), "server_databases": mysql.list_server_databases()}


@router.get("", response_model=list[DatabaseOut])
def list_databases(session: SessionDep, user: UserDep):
    return list(session.exec(select(Database).order_by(Database.name)).all())


@router.post("", response_model=DatabaseOut)
def create_database(payload: DatabaseCreate, session: SessionDep, user: UserDep):
    record = mysql.create(session, payload)
    audit(session, user, "database.create", record.name)
    return record


@router.get("/{db_id}/credentials")
def credentials(db_id: int, session: SessionDep, user: UserDep):
    record = mysql.get_record(session, db_id)
    audit(session, user, "database.credentials", record.name)
    return {"name": record.name, "username": record.username, "password": record.password}


@router.get("/{db_id}/size")
def database_size(db_id: int, session: SessionDep, user: UserDep):
    record = mysql.get_record(session, db_id)
    return {"name": record.name, "size": mysql.size(record.name)}


@router.post("/{db_id}/password", response_model=DatabaseOut)
def reset_password(db_id: int, payload: ResetPassword, session: SessionDep, user: UserDep):
    record = mysql.reset_password(session, db_id, payload.password)
    audit(session, user, "database.password", record.name)
    return record


@router.post("/{db_id}/backup")
def backup_database(db_id: int, session: SessionDep, user: UserDep):
    record = mysql.backup(session, db_id)
    audit(session, user, "database.backup", record.target)
    return record


@router.post("/{db_id}/import", response_model=Ok)
def import_sql(db_id: int, payload: ImportRequest, session: SessionDep, user: UserDep):
    mysql.import_sql(session, db_id, payload.sql_file)
    audit(session, user, "database.import", payload.sql_file)
    return Ok(message="SQL imported")


@router.delete("/{db_id}", response_model=Ok)
def drop_database(db_id: int, session: SessionDep, user: UserDep):
    record = mysql.get_record(session, db_id)
    name = record.name
    mysql.drop(session, db_id)
    audit(session, user, "database.drop", name)
    return Ok(message=f"Database {name} dropped")
