from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import SiteType


class LoginRequest(BaseModel):
    username: str
    password: str
    code: str = ""


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class TotpVerify(BaseModel):
    code: str


class SiteCreate(BaseModel):
    name: str
    site_type: SiteType = SiteType.static
    domains: list[str] = Field(default_factory=list)
    root: str = ""
    php_version: str = ""
    proxy_target: str = ""
    note: str = ""


class SiteUpdate(BaseModel):
    run_path: Optional[str] = None
    index_files: Optional[str] = None
    php_version: Optional[str] = None
    proxy_target: Optional[str] = None
    rewrite: Optional[str] = None
    extra_config: Optional[str] = None
    force_https: Optional[bool] = None
    note: Optional[str] = None


class DomainCreate(BaseModel):
    name: str
    port: int = 80


class SiteOut(BaseModel):
    id: int
    name: str
    site_type: SiteType
    root: str
    run_path: str
    index_files: str
    php_version: str
    proxy_target: str
    ssl_enabled: bool
    force_https: bool
    enabled: bool
    note: str
    created_at: datetime
    domains: list[str] = Field(default_factory=list)


class DatabaseCreate(BaseModel):
    name: str
    username: str = ""
    password: str = ""
    charset: str = "utf8mb4"
    note: str = ""


class DatabaseOut(BaseModel):
    id: int
    name: str
    username: str
    charset: str
    note: str
    created_at: datetime


class CronCreate(BaseModel):
    name: str
    schedule: str
    command: str
    enabled: bool = True


class CronUpdate(BaseModel):
    name: Optional[str] = None
    schedule: Optional[str] = None
    command: Optional[str] = None
    enabled: Optional[bool] = None


class PathRequest(BaseModel):
    path: str


class FileWrite(BaseModel):
    path: str
    content: str


class FileMove(BaseModel):
    source: str
    target: str


class ChmodRequest(BaseModel):
    path: str
    mode: str
    recursive: bool = False


class CertRequest(BaseModel):
    domains: list[str] = Field(default_factory=list)
    force_https: bool = False


class ServiceAction(BaseModel):
    name: str
    action: str


class Ok(BaseModel):
    ok: bool = True
    message: str = ""
