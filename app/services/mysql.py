from __future__ import annotations

import secrets
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import CommandFailed, Conflict, NotFound, PanelError
from app.models import BackupRecord, Database, utcnow
from app.schemas import DatabaseCreate
from app.services import shell
from app.services.paths import safe_identifier


def _base_argv(binary: str) -> list[str]:
    argv = [
        binary,
        f"--host={settings.mysql_host}",
        f"--port={settings.mysql_port}",
        f"--user={settings.mysql_user}",
    ]
    if settings.mysql_password:
        argv.append(f"--password={settings.mysql_password}")
    return argv


def base_argv(binary: str) -> list[str]:
    """Public alias: other services build mysql/mysqldump commands from this."""
    return _base_argv(binary)


def execute(sql: str, timeout: int = 60) -> shell.Result:
    result = shell.run(_base_argv(settings.mysql_bin) + ["-N", "-B", "-e", sql], timeout=timeout)
    if not result.ok:
        raise CommandFailed("MySQL command failed", result.output)
    return result


def server_available() -> bool:
    if settings.dry_run:
        return True
    return shell.run(_base_argv(settings.mysql_bin) + ["-N", "-B", "-e", "SELECT 1"]).ok


def list_server_databases() -> list[str]:
    if settings.dry_run:
        return []
    result = execute("SHOW DATABASES")
    skip = {"information_schema", "mysql", "performance_schema", "sys"}
    return [line.strip() for line in result.stdout.splitlines() if line.strip() not in skip]


def generate_password(length: int = 16) -> str:
    alphabet = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create(session: Session, payload: DatabaseCreate) -> Database:
    name = safe_identifier(payload.name)
    username = safe_identifier(payload.username or name)
    password = payload.password or generate_password()
    charset = safe_identifier(payload.charset.replace("-", "_"))

    if session.exec(select(Database).where(Database.name == name)).first():
        raise Conflict("Database already registered in SlimPanel")

    execute(
        f"CREATE DATABASE IF NOT EXISTS `{name}` "
        f"DEFAULT CHARACTER SET {charset} COLLATE {charset}_general_ci"
    )
    execute(
        f"CREATE USER IF NOT EXISTS '{username}'@'localhost' IDENTIFIED BY '{_escape(password)}'"
    )
    execute(f"GRANT ALL PRIVILEGES ON `{name}`.* TO '{username}'@'localhost'")
    execute("FLUSH PRIVILEGES")

    record = Database(
        name=name, username=username, password=password, charset=payload.charset, note=payload.note
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def reset_password(session: Session, db_id: int, password: str = "") -> Database:
    record = get_record(session, db_id)
    new_password = password or generate_password()
    execute(
        f"ALTER USER '{record.username}'@'localhost' IDENTIFIED BY '{_escape(new_password)}'"
    )
    execute("FLUSH PRIVILEGES")

    record.password = new_password
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def drop(session: Session, db_id: int) -> None:
    record = get_record(session, db_id)
    execute(f"DROP DATABASE IF EXISTS `{record.name}`")
    execute(f"DROP USER IF EXISTS '{record.username}'@'localhost'")
    session.delete(record)
    session.commit()


def size(name: str) -> int:
    if settings.dry_run:
        return 0
    result = execute(
        "SELECT IFNULL(SUM(data_length + index_length), 0) FROM information_schema.tables "
        f"WHERE table_schema = '{safe_identifier(name)}'"
    )
    try:
        return int(result.stdout.strip() or 0)
    except ValueError:
        return 0


def backup(session: Session, db_id: int) -> BackupRecord:
    record = get_record(session, db_id)
    settings.ensure_dirs()
    stamp = utcnow().strftime("%Y%m%d%H%M%S")
    target = settings.backup_dir / f"db_{record.name}_{stamp}.sql"

    result = shell.run(
        _base_argv(settings.mysqldump_bin) + ["--single-transaction", record.name],
        timeout=1800,
    )
    if not result.ok:
        raise CommandFailed("mysqldump failed", result.output)
    target.write_text(result.stdout)

    entry = BackupRecord(
        kind="database", target=record.name, filename=str(target), size=target.stat().st_size
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def import_sql(session: Session, db_id: int, sql_file: str) -> shell.Result:
    record = get_record(session, db_id)
    path = Path(sql_file)
    if not path.is_file():
        raise NotFound("SQL file not found")
    if path.stat().st_size > 512 * 1024 * 1024:
        raise PanelError("SQL file is larger than 512MB, import it from the shell instead")

    result = shell.run(
        _base_argv(settings.mysql_bin) + [record.name], stdin=path.read_text(), timeout=1800
    )
    if not result.ok:
        raise CommandFailed("SQL import failed", result.output)
    return result


def get_record(session: Session, db_id: int) -> Database:
    record = session.get(Database, db_id)
    if not record:
        raise NotFound("Database not found")
    return record


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")
