from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from app.deps import SessionDep, UserDep, audit
from app.models import Database
from app.schemas import DatabaseCreate, DatabaseOut, Ok
from app.services import dbengines, mysql

router = APIRouter(prefix="/databases", tags=["databases"])


class ResetPassword(BaseModel):
    password: str = ""


class ImportRequest(BaseModel):
    sql_file: str


class ServerIn(BaseModel):
    name: str
    engine: str
    host: str = "127.0.0.1"
    port: int = 3306
    username: str = ""
    password: str = ""
    note: str = ""


class PgCreate(BaseModel):
    name: str
    username: str = ""
    password: str = ""


class RedisConfigIn(BaseModel):
    key: str
    value: str


@router.get("/engines")
def engines(user: UserDep):
    return dbengines.engines()


@router.get("/status")
def server_status(user: UserDep):
    available = mysql.server_available()
    return {
        "available": available,
        # Listing needs a working connection, so skip it when there is none
        # rather than turning a known-offline server into a 500.
        "server_databases": mysql.list_server_databases() if available else [],
    }


# -------------------------------------------------------------- extra servers


@router.get("/servers")
def list_servers(session: SessionDep, user: UserDep):
    return dbengines.list_servers(session)


@router.post("/servers")
def create_server(payload: ServerIn, session: SessionDep, user: UserDep):
    row = dbengines.create_server(
        session, payload.name, payload.engine, payload.host, payload.port,
        payload.username, payload.password, payload.note,
    )
    audit(session, user, "database.server.create", row.name, detail=row.engine)
    return row.model_dump(exclude={"password"})


@router.post("/servers/{server_id}/test")
def test_server(server_id: int, session: SessionDep, user: UserDep):
    return dbengines.test_server(session, server_id)


@router.delete("/servers/{server_id}", response_model=Ok)
def delete_server(server_id: int, session: SessionDep, user: UserDep):
    row = dbengines.get_server(session, server_id)
    name = row.name
    dbengines.delete_server(session, server_id)
    audit(session, user, "database.server.delete", name)
    return Ok(message=f"Server {name} removed")


# ---------------------------------------------------------------- PostgreSQL


@router.get("/postgres")
def pg_list(user: UserDep):
    available = dbengines.pg_available()
    return {"available": available, "databases": dbengines.pg_list() if available else []}


@router.post("/postgres")
def pg_create(payload: PgCreate, session: SessionDep, user: UserDep):
    result = dbengines.pg_create(payload.name, payload.username, payload.password)
    audit(session, user, "database.pg.create", result["name"])
    return result


@router.post("/postgres/{name}/password")
def pg_password(name: str, payload: ResetPassword, session: SessionDep, user: UserDep):
    result = dbengines.pg_set_password(name, payload.password)
    audit(session, user, "database.pg.password", name)
    return result


@router.post("/postgres/{name}/backup")
def pg_backup(name: str, session: SessionDep, user: UserDep):
    record = dbengines.pg_backup(session, name)
    audit(session, user, "database.pg.backup", name)
    return record


@router.delete("/postgres/{name}", response_model=Ok)
def pg_drop(name: str, session: SessionDep, user: UserDep, drop_role: bool = True):
    dbengines.pg_drop(name, drop_role)
    audit(session, user, "database.pg.drop", name)
    return Ok(message=f"Database {name} dropped")


# ------------------------------------------------------------------- MongoDB


@router.get("/mongodb")
def mongo_list(user: UserDep):
    available = dbengines.mongo_available()
    return {"available": available, "databases": dbengines.mongo_list() if available else []}


@router.get("/mongodb/{name}/stats")
def mongo_stats(name: str, user: UserDep):
    return dbengines.mongo_stats(name)


@router.delete("/mongodb/{name}", response_model=Ok)
def mongo_drop(name: str, session: SessionDep, user: UserDep):
    dbengines.mongo_drop(name)
    audit(session, user, "database.mongo.drop", name)
    return Ok(message=f"Database {name} dropped")


# ---------------------------------------------------------------------- Redis


@router.get("/redis")
def redis_info(user: UserDep):
    if not dbengines.redis_available():
        return {"available": False}
    return {"available": True, **dbengines.redis_info()}


@router.get("/redis/config")
def redis_config(user: UserDep):
    return dbengines.redis_config()


@router.post("/redis/config")
def redis_set_config(payload: RedisConfigIn, session: SessionDep, user: UserDep):
    result = dbengines.redis_set_config(payload.key, payload.value)
    audit(session, user, "database.redis.config", payload.key, detail=payload.value)
    return result


@router.get("/redis/keys")
def redis_keys(user: UserDep, pattern: str = "*", limit: int = 200, database: int = 0):
    return dbengines.redis_keys(pattern, min(limit, 1000), database)


@router.delete("/redis/keys/{name}", response_model=Ok)
def redis_delete_key(name: str, session: SessionDep, user: UserDep, database: int = 0):
    result = dbengines.redis_delete_key(name, database)
    audit(session, user, "database.redis.del", name)
    return Ok(ok=result["deleted"], message="Key removed" if result["deleted"] else "Key not found")


@router.post("/redis/flush", response_model=Ok)
def redis_flush(session: SessionDep, user: UserDep, database: int | None = None):
    result = dbengines.redis_flush(database)
    audit(session, user, "database.redis.flush", result["flushed"])
    return Ok(message=f"Flushed {result['flushed']}")


# ---------------------------------------------------------- MySQL (the default)


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
