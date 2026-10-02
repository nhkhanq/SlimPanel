from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass, field, asdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = Path(os.environ.get("SLIMPANEL_CONFIG", BASE_DIR / "slimpanel.json"))


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    host: str = "0.0.0.0"
    port: int = 8899
    entry_path: str = ""
    secret_key: str = ""

    data_dir: Path = BASE_DIR / "data"
    www_root: Path = Path("/www/wwwroot")
    log_root: Path = Path("/www/wwwlogs")

    nginx_bin: str = "auto"
    nginx_reload_cmd: str = ""
    systemctl_bin: str = "systemctl"

    mysql_bin: str = "mysql"
    mysqldump_bin: str = "mysqldump"
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""

    psql_bin: str = "psql"
    pg_dump_bin: str = "pg_dump"
    pg_host: str = "127.0.0.1"
    pg_port: int = 5432
    pg_user: str = "postgres"
    pg_password: str = ""

    mongo_bin: str = "mongosh"
    mongo_uri: str = "mongodb://127.0.0.1:27017"

    redis_cli_bin: str = "redis-cli"
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""

    php_fpm_socket: str = "unix:/run/php/php{version}-fpm.sock"
    php_roots: list[str] = field(
        default_factory=lambda: ["/www/server/php", "/usr/local/php", "/etc/php"]
    )

    docker_bin: str = "docker"
    compose_bin: str = "docker compose"

    ftp_backend: str = "auto"
    pure_pw_bin: str = "pure-pw"
    pure_ftpd_passwd: str = "/www/server/pure-ftpd/etc/pureftpd.passwd"
    ftp_root: Path = Path("/www/wwwroot")

    sshd_config: str = "/etc/ssh/sshd_config"
    sshd_service: str = "auto"

    firewall_backend: str = "auto"

    cron_target: str = "/etc/cron.d/slimpanel"
    cron_user: str = "root"

    acme_bin: str = "certbot"
    acme_email: str = ""

    file_roots: list[str] = field(default_factory=lambda: ["/www/wwwroot", "/www/wwwlogs"])
    managed_services: list[str] = field(
        default_factory=lambda: [
            "nginx",
            "apache2",
            "httpd",
            "mysql",
            "mysqld",
            "mariadb",
            "redis",
            "redis-server",
            "memcached",
            "postgresql",
            "mongod",
            "docker",
            "pure-ftpd",
            "vsftpd",
            "supervisor",
            "supervisord",
            "crond",
            "cron",
        ]
    )

    monitor_enabled: bool = True
    monitor_interval: int = 60
    monitor_retention_days: int = 30

    session_max_age: int = 86400 * 7
    login_max_attempts: int = 5
    login_block_minutes: int = 30
    panel_ip_allowlist: list[str] = field(default_factory=list)
    panel_ssl: bool = False
    panel_basic_auth: str = ""

    recycle_bin: bool = True
    dry_run: bool = False

    @property
    def db_path(self) -> Path:
        return self.data_dir / "slimpanel.db"

    @property
    def vhost_dir(self) -> Path:
        return self.data_dir / "vhost" / "nginx"

    @property
    def rewrite_dir(self) -> Path:
        return self.data_dir / "vhost" / "rewrite"

    @property
    def upstream_dir(self) -> Path:
        return self.data_dir / "vhost" / "upstream"

    @property
    def auth_dir(self) -> Path:
        return self.data_dir / "vhost" / "auth"

    @property
    def cert_dir(self) -> Path:
        return self.data_dir / "cert"

    @property
    def panel_cert_dir(self) -> Path:
        return self.data_dir / "cert" / "_panel"

    @property
    def backup_dir(self) -> Path:
        return self.data_dir / "backup"

    @property
    def recycle_dir(self) -> Path:
        return self.data_dir / "recycle"

    @property
    def project_dir(self) -> Path:
        return self.data_dir / "projects"

    @property
    def cron_file(self) -> Path:
        return self.data_dir / "crontab"

    @property
    def cron_log_dir(self) -> Path:
        return self.data_dir / "logs" / "cron"

    @property
    def task_log_dir(self) -> Path:
        return self.data_dir / "logs" / "tasks"

    @property
    def acme_webroot(self) -> Path:
        return self.data_dir / "acme-challenge"

    def ensure_dirs(self) -> None:
        for path in (
            self.data_dir,
            self.vhost_dir,
            self.rewrite_dir,
            self.upstream_dir,
            self.auth_dir,
            self.cert_dir,
            self.panel_cert_dir,
            self.backup_dir,
            self.recycle_dir,
            self.project_dir,
            self.cron_log_dir,
            self.task_log_dir,
            self.acme_webroot,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        raw = asdict(self)
        return {k: str(v) if isinstance(v, Path) else v for k, v in raw.items()}


_PATH_FIELDS = {"data_dir", "www_root", "log_root", "ftp_root"}
_INT_FIELDS = {
    "port",
    "mysql_port",
    "pg_port",
    "redis_port",
    "session_max_age",
    "monitor_interval",
    "monitor_retention_days",
    "login_max_attempts",
    "login_block_minutes",
}
_LIST_FIELDS = {"file_roots", "managed_services", "php_roots", "panel_ip_allowlist"}
_BOOL_FIELDS = {"dry_run", "monitor_enabled", "recycle_bin", "panel_ssl"}


def _load_file() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (OSError, ValueError):
        return {}


def load_settings() -> Settings:
    values = _load_file()

    for name in Settings.__dataclass_fields__:
        env = os.environ.get(f"SLIMPANEL_{name.upper()}")
        if env is not None:
            values[name] = env

    kwargs: dict = {}
    for name, raw in values.items():
        if name not in Settings.__dataclass_fields__:
            continue
        if name in _PATH_FIELDS:
            kwargs[name] = Path(raw)
        elif name in _INT_FIELDS:
            kwargs[name] = int(raw)
        elif name in _LIST_FIELDS:
            kwargs[name] = [p for p in raw.split(",") if p] if isinstance(raw, str) else list(raw)
        elif name in _BOOL_FIELDS:
            kwargs[name] = raw if isinstance(raw, bool) else str(raw).lower() in {"1", "true", "yes", "on"}
        else:
            kwargs[name] = raw

    settings = Settings(**kwargs)
    settings.dry_run = _env_bool("SLIMPANEL_DRY_RUN", settings.dry_run)

    # FTP homes live under the web root unless told otherwise; defaulting them
    # independently means moving www_root breaks FTP user creation.
    if "ftp_root" not in values:
        settings.ftp_root = settings.www_root

    if not settings.secret_key:
        settings.secret_key = _persisted_secret()

    settings.entry_path = "/" + settings.entry_path.strip("/") if settings.entry_path.strip("/") else ""
    return settings


def save_settings(updates: dict) -> dict:
    """Merge updates into slimpanel.json. Takes effect on the next restart."""
    current = _load_file()
    for key, value in updates.items():
        if key in Settings.__dataclass_fields__ and key != "secret_key":
            current[key] = str(value) if isinstance(value, Path) else value
    CONFIG_FILE.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass
    return current


def _persisted_secret() -> str:
    key_file = Path(os.environ.get("SLIMPANEL_DATA_DIR", BASE_DIR / "data")) / "secret.key"
    if key_file.exists():
        return key_file.read_text().strip()
    key_file.parent.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_hex(32)
    key_file.write_text(secret)
    key_file.chmod(0o600)
    return secret


settings = load_settings()
