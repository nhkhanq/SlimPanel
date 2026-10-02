from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SiteType(str, Enum):
    php = "php"
    static = "static"
    proxy = "proxy"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    totp_secret: Optional[str] = None
    totp_enabled: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    password_changed_at: datetime = Field(default_factory=utcnow)


class Site(SQLModel, table=True):
    __tablename__ = "sites"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    site_type: SiteType = Field(default=SiteType.static)
    root: str
    run_path: str = ""
    index_files: str = "index.html index.htm"
    php_version: str = ""
    proxy_target: str = ""
    rewrite: str = ""
    extra_config: str = ""
    ssl_enabled: bool = False
    force_https: bool = False
    enabled: bool = True
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class Domain(SQLModel, table=True):
    __tablename__ = "domains"

    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: int = Field(index=True, foreign_key="sites.id")
    name: str = Field(index=True)
    port: int = 80


class Database(SQLModel, table=True):
    __tablename__ = "databases"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    username: str
    password: str
    charset: str = "utf8mb4"
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class CronJob(SQLModel, table=True):
    __tablename__ = "cron_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    schedule: str
    command: str
    enabled: bool = True
    last_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)


class BackupRecord(SQLModel, table=True):
    __tablename__ = "backups"

    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str
    target: str
    filename: str
    size: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class Certificate(SQLModel, table=True):
    __tablename__ = "certificates"

    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: int = Field(index=True, foreign_key="sites.id")
    domains: str
    issuer: str = "letsencrypt"
    not_after: Optional[datetime] = None
    cert_path: str = ""
    key_path: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class LoginLog(SQLModel, table=True):
    __tablename__ = "login_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    ip: str = ""
    success: bool = False
    detail: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class OperationLog(SQLModel, table=True):
    __tablename__ = "operation_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = ""
    action: str = ""
    target: str = ""
    success: bool = True
    detail: str = ""
    created_at: datetime = Field(default_factory=utcnow)
