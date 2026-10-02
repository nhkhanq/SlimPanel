from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import CommandFailed, Conflict, NotFound, PanelError
from app.models import BackupRecord, DbServer, utcnow
from app.services import shell
from app.services.mysql import generate_password
from app.services.paths import safe_identifier

ENGINES = ("mysql", "postgres", "mongodb", "redis")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def engines() -> list[dict]:
    """Which engines this host can actually talk to."""
    return [
        {
            "key": "mysql",
            "label": "MySQL / MariaDB",
            "client": settings.mysql_bin,
            "available": bool(shutil.which(settings.mysql_bin)) or settings.dry_run,
            "default_port": 3306,
        },
        {
            "key": "postgres",
            "label": "PostgreSQL",
            "client": settings.psql_bin,
            "available": bool(shutil.which(settings.psql_bin)) or settings.dry_run,
            "default_port": 5432,
        },
        {
            "key": "mongodb",
            "label": "MongoDB",
            "client": settings.mongo_bin,
            "available": bool(shutil.which(settings.mongo_bin)) or settings.dry_run,
            "default_port": 27017,
        },
        {
            "key": "redis",
            "label": "Redis",
            "client": settings.redis_cli_bin,
            "available": bool(shutil.which(settings.redis_cli_bin)) or settings.dry_run,
            "default_port": 6379,
        },
    ]


# --------------------------------------------------------------- extra servers


def list_servers(session: Session) -> list[dict]:
    rows = session.exec(select(DbServer).order_by(DbServer.id)).all()
    return [
        {**row.model_dump(exclude={"password"}), "has_password": bool(row.password)} for row in rows
    ]


def get_server(session: Session, server_id: int) -> DbServer:
    row = session.get(DbServer, server_id)
    if not row:
        raise NotFound("Database server not found")
    return row


def create_server(
    session: Session,
    name: str,
    engine: str,
    host: str,
    port: int,
    username: str = "",
    password: str = "",
    note: str = "",
) -> DbServer:
    if engine not in ENGINES:
        raise PanelError(f"Engine must be one of {', '.join(ENGINES)}")
    if not 1 <= port <= 65535:
        raise PanelError("Port out of range")
    if session.exec(select(DbServer).where(DbServer.name == name.strip())).first():
        raise Conflict("A server with that name already exists")

    row = DbServer(
        name=name.strip(),
        engine=engine,
        host=host.strip() or "127.0.0.1",
        port=port,
        username=username.strip(),
        password=password,
        note=note,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def delete_server(session: Session, server_id: int) -> None:
    session.delete(get_server(session, server_id))
    session.commit()


def test_server(session: Session, server_id: int) -> dict:
    row = get_server(session, server_id)
    probe = {
        "mysql": lambda: shell.run(
            [settings.mysql_bin, f"--host={row.host}", f"--port={row.port}",
             f"--user={row.username}", *([f"--password={row.password}"] if row.password else []),
             "-N", "-B", "-e", "SELECT 1"],
            timeout=20,
        ),
        "postgres": lambda: shell.run(
            [settings.psql_bin, "-h", row.host, "-p", str(row.port), "-U", row.username,
             "-tAc", "SELECT 1"],
            timeout=20,
            env={**_pg_env(row.password), "PATH": "/usr/bin:/bin:/usr/local/bin"},
        ),
        "mongodb": lambda: shell.run(
            [settings.mongo_bin, f"mongodb://{row.host}:{row.port}", "--quiet", "--eval",
             "db.runCommand({ping:1})"],
            timeout=20,
        ),
        "redis": lambda: shell.run(
            [settings.redis_cli_bin, "-h", row.host, "-p", str(row.port),
             *(["-a", row.password] if row.password else []), "PING"],
            timeout=20,
        ),
    }[row.engine]
    result = probe()
    return {"ok": result.ok, "output": result.output[:2000]}


def _pg_env(password: str) -> dict[str, str]:
    return {"PGPASSWORD": password} if password else {}


# ------------------------------------------------------------------ PostgreSQL


def _psql(sql: str, database: str = "postgres", timeout: int = 60) -> shell.Result:
    argv = [
        settings.psql_bin,
        "-h", settings.pg_host,
        "-p", str(settings.pg_port),
        "-U", settings.pg_user,
        "-d", database,
        "-tAc", sql,
    ]
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", **_pg_env(settings.pg_password)}
    result = shell.run(argv, timeout=timeout, env=env)
    if not result.ok:
        raise CommandFailed("PostgreSQL command failed", result.output)
    return result


def pg_available() -> bool:
    if settings.dry_run:
        return True
    if not shutil.which(settings.psql_bin):
        return False
    try:
        _psql("SELECT 1")
    except CommandFailed:
        return False
    return True


def pg_list() -> list[dict]:
    if settings.dry_run:
        return []
    result = _psql(
        "SELECT datname, pg_catalog.pg_get_userbyid(datdba), "
        "pg_database_size(datname) FROM pg_database "
        "WHERE datistemplate = false ORDER BY datname"
    )
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split("|")
        if len(parts) >= 3:
            rows.append(
                {"name": parts[0], "owner": parts[1], "size": int(parts[2] or 0)}
            )
    return rows


def pg_create(name: str, username: str = "", password: str = "") -> dict:
    database = safe_identifier(name)
    role = safe_identifier(username or name)
    secret = password or generate_password(16)

    _psql(f"CREATE ROLE \"{role}\" LOGIN PASSWORD '{secret.replace(chr(39), chr(39) * 2)}'")
    _psql(f'CREATE DATABASE "{database}" OWNER "{role}"')
    _psql(f'GRANT ALL PRIVILEGES ON DATABASE "{database}" TO "{role}"')
    return {"name": database, "username": role, "password": secret}


def pg_drop(name: str, drop_role: bool = True) -> dict:
    database = safe_identifier(name)
    owner = _psql(
        f"SELECT pg_catalog.pg_get_userbyid(datdba) FROM pg_database WHERE datname = '{database}'"
    ).stdout.strip()
    _psql(
        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{database}'"
    )
    _psql(f'DROP DATABASE IF EXISTS "{database}"')
    if drop_role and owner and owner not in {"postgres", settings.pg_user}:
        try:
            _psql(f'DROP ROLE IF EXISTS "{owner}"')
        except CommandFailed:
            pass
    return {"name": database, "dropped": True}


def pg_set_password(name: str, password: str = "") -> dict:
    database = safe_identifier(name)
    owner = _psql(
        f"SELECT pg_catalog.pg_get_userbyid(datdba) FROM pg_database WHERE datname = '{database}'"
    ).stdout.strip()
    if not owner:
        raise NotFound("Database not found")
    secret = password or generate_password(16)
    _psql(f"ALTER ROLE \"{owner}\" PASSWORD '{secret.replace(chr(39), chr(39) * 2)}'")
    return {"name": database, "username": owner, "password": secret}


def pg_backup(session: Session, name: str) -> BackupRecord:
    database = safe_identifier(name)
    settings.ensure_dirs()
    stamp = utcnow().strftime("%Y%m%d%H%M%S")
    target = settings.backup_dir / f"pg_{database}_{stamp}.sql"

    result = shell.run(
        [settings.pg_dump_bin, "-h", settings.pg_host, "-p", str(settings.pg_port),
         "-U", settings.pg_user, database],
        timeout=1800,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", **_pg_env(settings.pg_password)},
    )
    if not result.ok:
        raise CommandFailed("pg_dump failed", result.output)
    target.write_text(result.stdout)

    record = BackupRecord(
        kind="postgres", target=database, filename=str(target), size=target.stat().st_size
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


# --------------------------------------------------------------------- MongoDB


def _mongo(script: str, timeout: int = 60) -> shell.Result:
    result = shell.run(
        [settings.mongo_bin, settings.mongo_uri, "--quiet", "--eval", script], timeout=timeout
    )
    if not result.ok:
        raise CommandFailed("MongoDB command failed", result.output)
    return result


def mongo_available() -> bool:
    if settings.dry_run:
        return True
    if not shutil.which(settings.mongo_bin):
        return False
    try:
        _mongo("db.runCommand({ping:1})")
    except CommandFailed:
        return False
    return True


def mongo_list() -> list[dict]:
    if settings.dry_run:
        return []
    result = _mongo("JSON.stringify(db.adminCommand({listDatabases:1}))")
    try:
        data = json.loads(result.stdout.strip() or "{}")
    except ValueError:
        return []
    return [
        {"name": row.get("name", ""), "size": row.get("sizeOnDisk", 0), "empty": row.get("empty", False)}
        for row in data.get("databases", [])
    ]


def mongo_drop(name: str) -> dict:
    database = safe_identifier(name)
    _mongo(f'db.getSiblingDB("{database}").dropDatabase()')
    return {"name": database, "dropped": True}


def mongo_stats(name: str) -> dict:
    database = safe_identifier(name)
    result = _mongo(f'JSON.stringify(db.getSiblingDB("{database}").stats())')
    try:
        return json.loads(result.stdout.strip() or "{}")
    except ValueError:
        return {}


# ----------------------------------------------------------------------- Redis


def _redis(args: list[str], timeout: int = 30) -> shell.Result:
    argv = [settings.redis_cli_bin, "-h", settings.redis_host, "-p", str(settings.redis_port)]
    if settings.redis_password:
        argv += ["-a", settings.redis_password, "--no-auth-warning"]
    return shell.run(argv + args, timeout=timeout)


def redis_available() -> bool:
    if settings.dry_run:
        return True
    if not shutil.which(settings.redis_cli_bin):
        return False
    return "PONG" in _redis(["PING"]).output


def redis_info() -> dict:
    result = _redis(["INFO"])
    if not result.ok:
        raise CommandFailed("redis-cli INFO failed", result.output)

    parsed: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line and not line.startswith("#"):
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip()

    keyspace = []
    for key, value in parsed.items():
        if key.startswith("db") and "keys=" in value:
            parts = dict(pair.split("=") for pair in value.split(",") if "=" in pair)
            keyspace.append(
                {
                    "db": key,
                    "keys": int(parts.get("keys", 0)),
                    "expires": int(parts.get("expires", 0)),
                }
            )

    return {
        "version": parsed.get("redis_version", ""),
        "uptime_seconds": int(parsed.get("uptime_in_seconds", 0) or 0),
        "connected_clients": int(parsed.get("connected_clients", 0) or 0),
        "used_memory": int(parsed.get("used_memory", 0) or 0),
        "used_memory_human": parsed.get("used_memory_human", ""),
        "used_memory_peak": int(parsed.get("used_memory_peak", 0) or 0),
        "maxmemory": int(parsed.get("maxmemory", 0) or 0),
        "maxmemory_policy": parsed.get("maxmemory_policy", ""),
        "total_commands": int(parsed.get("total_commands_processed", 0) or 0),
        "hits": int(parsed.get("keyspace_hits", 0) or 0),
        "misses": int(parsed.get("keyspace_misses", 0) or 0),
        "evicted": int(parsed.get("evicted_keys", 0) or 0),
        "keyspace": keyspace,
        "role": parsed.get("role", ""),
    }


def redis_config() -> list[dict]:
    result = _redis(["CONFIG", "GET", "*"])
    lines = result.stdout.splitlines()
    rows = []
    for index in range(0, len(lines) - 1, 2):
        rows.append({"key": lines[index], "value": lines[index + 1]})
    interesting = {
        "maxmemory", "maxmemory-policy", "appendonly", "save", "requirepass",
        "timeout", "databases", "bind", "port", "tcp-backlog",
    }
    rows = [row for row in rows if row["key"] in interesting]
    for row in rows:
        if row["key"] == "requirepass" and row["value"]:
            row["value"] = "********"
    return sorted(rows, key=lambda row: row["key"])


def redis_set_config(key: str, value: str) -> dict:
    allowed = {"maxmemory", "maxmemory-policy", "appendonly", "timeout", "save"}
    if key not in allowed:
        raise PanelError(f"{key} is not an editable Redis setting")
    if any(ch in str(value) for ch in ";\n`$"):
        raise PanelError("Invalid value")
    result = _redis(["CONFIG", "SET", key, str(value)])
    if not result.ok:
        raise CommandFailed("CONFIG SET failed", result.output)
    _redis(["CONFIG", "REWRITE"])
    return {"key": key, "value": value}


def redis_flush(database: int | None = None) -> dict:
    args = ["FLUSHALL"] if database is None else ["-n", str(database), "FLUSHDB"]
    result = _redis(args)
    if not result.ok:
        raise CommandFailed("Flush failed", result.output)
    return {"flushed": "all" if database is None else f"db{database}"}


def redis_keys(pattern: str = "*", limit: int = 200, database: int = 0) -> list[dict]:
    if any(ch in pattern for ch in " ;\n`$"):
        raise PanelError("Invalid pattern")
    result = _redis(["-n", str(database), "--scan", "--pattern", pattern], timeout=60)
    names = [line.strip() for line in result.stdout.splitlines() if line.strip()][:limit]

    rows = []
    for name in names:
        kind = _redis(["-n", str(database), "TYPE", name]).stdout.strip()
        ttl = _redis(["-n", str(database), "TTL", name]).stdout.strip()
        rows.append({"key": name, "type": kind, "ttl": int(ttl) if ttl.lstrip("-").isdigit() else -1})
    return rows


def redis_delete_key(name: str, database: int = 0) -> dict:
    if any(ch in name for ch in " ;\n`$"):
        raise PanelError("Invalid key name")
    result = _redis(["-n", str(database), "DEL", name])
    return {"deleted": result.stdout.strip() == "1"}


def redis_config_file() -> dict:
    for candidate in ("/etc/redis/redis.conf", "/www/server/redis/redis.conf", "/etc/redis.conf"):
        path = Path(candidate)
        if path.is_file():
            return {"path": str(path), "content": path.read_text(errors="replace")}
    raise NotFound("No redis.conf found on this host")
