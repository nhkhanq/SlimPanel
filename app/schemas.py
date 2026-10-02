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
    upstream_name: str = ""
    project_id: Optional[int] = None
    group_id: Optional[int] = None
    note: str = ""


class SiteUpdate(BaseModel):
    site_type: Optional[SiteType] = None
    run_path: Optional[str] = None
    index_files: Optional[str] = None
    php_version: Optional[str] = None
    proxy_target: Optional[str] = None
    upstream_name: Optional[str] = None
    project_id: Optional[int] = None
    group_id: Optional[int] = None
    rewrite: Optional[str] = None
    extra_config: Optional[str] = None
    extra_headers: Optional[str] = None
    error_page: Optional[str] = None
    default_page: Optional[str] = None
    force_https: Optional[bool] = None
    hsts: Optional[bool] = None
    ssl_protocols: Optional[str] = None
    deny_extensions: Optional[str] = None
    anti_leech_enabled: Optional[bool] = None
    anti_leech_extensions: Optional[str] = None
    anti_leech_allow: Optional[str] = None
    anti_leech_return: Optional[str] = None
    limit_rate: Optional[int] = None
    limit_conn: Optional[int] = None
    limit_req: Optional[int] = None
    client_max_body: Optional[str] = None
    gzip_enabled: Optional[bool] = None
    cache_enabled: Optional[bool] = None
    cache_expires: Optional[str] = None
    waf_enabled: Optional[bool] = None
    ip_deny: Optional[str] = None
    ip_allow: Optional[str] = None
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
    upstream_name: str = ""
    project_id: Optional[int] = None
    group_id: Optional[int] = None
    ssl_enabled: bool
    force_https: bool
    hsts: bool = False
    ssl_protocols: str = "TLSv1.2 TLSv1.3"
    enabled: bool
    note: str
    deny_extensions: str = ""
    anti_leech_enabled: bool = False
    anti_leech_extensions: str = ""
    anti_leech_allow: str = ""
    anti_leech_return: str = "404"
    limit_rate: int = 0
    limit_conn: int = 0
    limit_req: int = 0
    client_max_body: str = "50m"
    gzip_enabled: bool = True
    cache_enabled: bool = False
    cache_expires: str = "30d"
    waf_enabled: bool = False
    extra_config: str = ""
    extra_headers: str = ""
    error_page: str = ""
    ip_deny: str = ""
    ip_allow: str = ""
    created_at: datetime
    domains: list[str] = Field(default_factory=list)
    group_name: str = ""
    ssl_expires_at: Optional[datetime] = None


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
