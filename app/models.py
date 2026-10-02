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
    node = "node"
    python = "python"
    java = "java"
    go = "go"
    dotnet = "dotnet"
    redirect = "redirect"
    balance = "balance"


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
    hsts: bool = False
    ssl_protocols: str = "TLSv1.2 TLSv1.3"
    enabled: bool = True
    note: str = ""
    group_id: Optional[int] = Field(default=None, index=True)

    # upstream / project binding
    upstream_name: str = ""
    project_id: Optional[int] = None

    # access control, the knobs aaPanel puts on each site
    deny_extensions: str = ""
    anti_leech_enabled: bool = False
    anti_leech_extensions: str = "jpg,jpeg,png,gif,webp,avif,bmp,ico,mp4,webm,zip,rar"
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
    error_page: str = ""
    default_page: str = ""
    extra_headers: str = ""
    ip_deny: str = ""
    ip_allow: str = ""
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)


class SiteGroup(SQLModel, table=True):
    __tablename__ = "site_groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
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


class Redirect(SQLModel, table=True):
    """A site redirect: 301/302 from a path or domain to somewhere else."""

    __tablename__ = "redirects"

    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: int = Field(index=True, foreign_key="sites.id")
    name: str = ""
    kind: str = "path"  # path | domain
    source: str = "/"
    target: str = ""
    code: int = 301
    keep_path: bool = True
    keep_query: bool = True
    enabled: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class ProxyRule(SQLModel, table=True):
    """A reverse proxy on one location of a site."""

    __tablename__ = "proxy_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: int = Field(index=True, foreign_key="sites.id")
    name: str = ""
    location: str = "/"
    target: str = ""
    host_header: str = "$host"
    cache_enabled: bool = False
    cache_time: int = 3600
    websocket: bool = True
    replace_rules: str = ""  # from|to, one per line
    extra: str = ""
    enabled: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class DirAuth(SQLModel, table=True):
    """HTTP basic auth on a site directory."""

    __tablename__ = "dir_auths"

    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: int = Field(index=True, foreign_key="sites.id")
    name: str
    location: str = "/"
    username: str = ""
    enabled: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class Upstream(SQLModel, table=True):
    """A load balancing pool."""

    __tablename__ = "upstreams"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    method: str = "round_robin"  # round_robin | ip_hash | least_conn
    keepalive: int = 32
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class UpstreamNode(SQLModel, table=True):
    __tablename__ = "upstream_nodes"

    id: Optional[int] = Field(default=None, primary_key=True)
    upstream_id: int = Field(index=True, foreign_key="upstreams.id")
    address: str
    weight: int = 1
    max_fails: int = 3
    fail_timeout: int = 30
    backup: bool = False
    down: bool = False


class Project(SQLModel, table=True):
    """A Node / Python / Java / Go / .NET app supervised by systemd."""

    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    runtime: str = "node"  # node | python | java | go | dotnet | other
    path: str = ""
    command: str = ""
    port: int = 0
    user: str = "root"
    env: str = ""  # KEY=value, one per line
    autostart: bool = True
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class FtpUser(SQLModel, table=True):
    __tablename__ = "ftp_users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str = ""
    home: str = ""
    quota_mb: int = 0
    enabled: bool = True
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class FirewallRule(SQLModel, table=True):
    """A port rule mirrored into ufw / firewalld / iptables."""

    __tablename__ = "firewall_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = ""
    port: str = ""  # 80, or 8000:8100
    protocol: str = "tcp"  # tcp | udp | both
    action: str = "accept"  # accept | drop
    source: str = ""  # empty means anywhere
    direction: str = "in"
    enabled: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class IpRule(SQLModel, table=True):
    """An IP allow/deny entry, applied to the firewall or to the panel itself."""

    __tablename__ = "ip_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    address: str = Field(index=True)
    action: str = "drop"  # accept | drop
    scope: str = "server"  # server | panel
    note: str = ""
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)


class MonitorSample(SQLModel, table=True):
    __tablename__ = "monitor_samples"

    id: Optional[int] = Field(default=None, primary_key=True)
    taken_at: datetime = Field(default_factory=utcnow, index=True)
    cpu: float = 0.0
    memory: float = 0.0
    swap: float = 0.0
    load1: float = 0.0
    disk_percent: float = 0.0
    disk_read: int = 0
    disk_write: int = 0
    net_sent: int = 0
    net_recv: int = 0
    net_up: float = 0.0
    net_down: float = 0.0
    processes: int = 0
    connections: int = 0


class NotifyChannel(SQLModel, table=True):
    __tablename__ = "notify_channels"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    kind: str = "webhook"  # webhook | email | telegram | dingtalk | wecom | slack
    config: str = "{}"  # JSON
    enabled: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class AlertRule(SQLModel, table=True):
    __tablename__ = "alert_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    metric: str = "cpu"  # cpu | memory | disk | load | cert_expiry | site_down | service_down
    operator: str = ">"
    threshold: float = 90.0
    target: str = ""
    channel_id: Optional[int] = None
    cooldown_minutes: int = 60
    enabled: bool = True
    last_fired_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)


class AlertEvent(SQLModel, table=True):
    __tablename__ = "alert_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: Optional[int] = Field(default=None, index=True)
    title: str = ""
    body: str = ""
    delivered: bool = False
    detail: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    key_id: str = Field(index=True, unique=True)
    secret: str = ""
    secret_hash: str = ""
    allow_ips: str = ""
    enabled: bool = True
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)


class RecycleItem(SQLModel, table=True):
    __tablename__ = "recycle_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    original_path: str
    stored_path: str
    is_dir: bool = False
    size: int = 0
    deleted_at: datetime = Field(default_factory=utcnow)


class BackupTarget(SQLModel, table=True):
    """Where backups are copied after they are made."""

    __tablename__ = "backup_targets"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    kind: str = "local"  # local | s3 | ftp | sftp | webdav | rsync
    config: str = "{}"
    enabled: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class DbServer(SQLModel, table=True):
    """An extra database server, local or remote."""

    __tablename__ = "db_servers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    engine: str = "mysql"  # mysql | postgres | mongodb | redis
    host: str = "127.0.0.1"
    port: int = 3306
    username: str = ""
    password: str = ""
    is_default: bool = False
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class TaskRecord(SQLModel, table=True):
    """A long job run in the background, so the UI never blocks on it."""

    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    kind: str = "shell"
    status: str = "pending"  # pending | running | done | failed | cancelled
    progress: int = 0
    detail: str = ""
    log_file: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)


class PanelSetting(SQLModel, table=True):
    """Small key/value store for panel preferences the UI owns."""

    __tablename__ = "panel_settings"

    key: str = Field(primary_key=True)
    value: str = ""
    updated_at: datetime = Field(default_factory=utcnow)


class LoginAttempt(SQLModel, table=True):
    __tablename__ = "login_attempts"

    id: Optional[int] = Field(default=None, primary_key=True)
    ip: str = Field(index=True)
    username: str = ""
    created_at: datetime = Field(default_factory=utcnow, index=True)
