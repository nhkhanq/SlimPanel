from __future__ import annotations

import re
import shutil
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.errors import NotFound, PanelError
from app.models import CronJob, Database, Domain, Site, SiteType
from app.services import nginx
from app.services.paths import safe_identifier, safe_site_name

DEFAULT_PANEL_DIR = Path("/www/server/panel")
DEFAULT_CRON_DIR = Path("/www/server/cron")

PHP_INCLUDE = re.compile(r"include\s+enable-php-(\d+)\.conf")
PROXY_PASS = re.compile(r"^\s*proxy_pass\s+([^;]+);", re.M)
ROOT_DIRECTIVE = re.compile(r"^\s*root\s+([^;]+);", re.M)
INDEX_DIRECTIVE = re.compile(r"^\s*index\s+([^;]+);", re.M)
SERVER_NAME = re.compile(r"^\s*server_name\s+([^;]+);", re.M)
SSL_CERT = re.compile(r"^\s*ssl_certificate\s+([^;]+);", re.M)
HTTPS_REDIRECT = re.compile(r"^\s*rewrite\s+\^\(/\.\*\)\$\s+https://", re.M)

WEEKDAY_TYPES = {"week": "week", "month": "month"}


@dataclass
class Source:
    panel_dir: Path = DEFAULT_PANEL_DIR
    cron_dir: Path = DEFAULT_CRON_DIR

    @property
    def db_path(self) -> Path:
        return self.panel_dir / "data" / "default.db"

    @property
    def vhost_dir(self) -> Path:
        return self.panel_dir / "vhost" / "nginx"

    @property
    def cert_dir(self) -> Path:
        return self.panel_dir / "vhost" / "cert"

    @property
    def rewrite_dir(self) -> Path:
        return self.panel_dir / "vhost" / "rewrite"

    def check(self) -> None:
        if not self.db_path.is_file():
            raise NotFound(f"aaPanel database not found at {self.db_path}")


@dataclass
class Item:
    kind: str
    name: str
    action: str
    reason: str = ""
    data: dict = field(default_factory=dict)


@dataclass
class Report:
    items: list[Item] = field(default_factory=list)
    tables: dict[str, list[str]] = field(default_factory=dict)

    def add(self, item: Item) -> None:
        self.items.append(item)

    def of(self, kind: str, action: str = "") -> list[Item]:
        return [i for i in self.items if i.kind == kind and (not action or i.action == action)]

    def summary(self) -> dict:
        counts: dict[str, dict[str, int]] = {}
        for item in self.items:
            counts.setdefault(item.kind, {}).setdefault(item.action, 0)
            counts[item.kind][item.action] += 1
        return counts

    def to_dict(self) -> dict:
        return {
            "summary": self.summary(),
            "tables": self.tables,
            "items": [vars(item) for item in self.items],
        }


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
    except sqlite3.DatabaseError:
        return []
    return [row["name"] for row in rows]


def inspect(source: Source) -> dict:
    source.check()
    with connect(source.db_path) as conn:
        names = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        schema = {name: table_columns(conn, name) for name in names}
        counts = {}
        for name in names:
            try:
                counts[name] = conn.execute(f"SELECT COUNT(*) FROM '{name}'").fetchone()[0]
            except sqlite3.DatabaseError:
                counts[name] = -1
    return {"path": str(source.db_path), "tables": schema, "rows": counts}


def _rows(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    if not table_columns(conn, table):
        return []
    return conn.execute(f"SELECT * FROM '{table}'").fetchall()


def _value(row: sqlite3.Row, *names: str, default=None):
    keys = row.keys()
    for name in names:
        if name in keys and row[name] is not None:
            return row[name]
    return default


def parse_vhost(text: str) -> dict:
    active = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )

    parsed: dict = {
        "root": "",
        "index": "",
        "domains": [],
        "php_version": "",
        "proxy_target": "",
        "ssl": False,
        "force_https": False,
    }

    root = ROOT_DIRECTIVE.search(active)
    if root:
        parsed["root"] = root.group(1).strip()

    index = INDEX_DIRECTIVE.search(active)
    if index:
        parsed["index"] = " ".join(index.group(1).split())

    names = SERVER_NAME.search(active)
    if names:
        parsed["domains"] = names.group(1).split()

    php = PHP_INCLUDE.search(active)
    if php:
        raw = php.group(1)
        parsed["php_version"] = raw if raw == "00" else f"{raw[0]}.{raw[1:]}"

    proxy = PROXY_PASS.search(active)
    if proxy:
        parsed["proxy_target"] = proxy.group(1).strip()

    parsed["ssl"] = bool(SSL_CERT.search(active))
    parsed["force_https"] = bool(HTTPS_REDIRECT.search(active))
    return parsed


def site_type_of(parsed: dict) -> SiteType:
    if parsed["proxy_target"]:
        return SiteType.proxy
    if parsed["php_version"] and parsed["php_version"] != "00":
        return SiteType.php
    return SiteType.static


def cron_schedule(row: sqlite3.Row) -> str:
    kind = str(_value(row, "type", default="day"))
    where = str(_value(row, "where1", default="") or "")
    hour = int(_value(row, "where_hour", default=0) or 0)
    minute = int(_value(row, "where_minute", default=0) or 0)

    if kind == "minute-n":
        return f"*/{where or 1} * * * *"
    if kind == "hour":
        return f"{minute} * * * *"
    if kind == "hour-n":
        return f"{minute} */{where or 1} * * *"
    if kind == "day":
        return f"{minute} {hour} * * *"
    if kind == "day-n":
        return f"{minute} {hour} */{where or 1} * *"
    if kind == "week":
        return f"{minute} {hour} * * {where or 0}"
    if kind == "month":
        return f"{minute} {hour} {where or 1} * *"
    return f"{minute} {hour} * * *"


def plan(session: Session, source: Source) -> Report:
    source.check()
    report = Report()

    with connect(source.db_path) as conn:
        report.tables = {
            name: table_columns(conn, name) for name in ("sites", "domain", "databases", "crontab")
        }
        _plan_sites(session, conn, source, report)
        _plan_databases(session, conn, report)
        _plan_crons(session, conn, source, report)

    return report


def _plan_sites(
    session: Session, conn: sqlite3.Connection, source: Source, report: Report
) -> None:
    existing = {site.name for site in session.exec(select(Site)).all()}
    domains_by_site: dict[int, list[str]] = {}
    for row in _rows(conn, "domain"):
        pid = _value(row, "pid", "site_id")
        name = _value(row, "name", default="")
        if pid is not None and name:
            domains_by_site.setdefault(int(pid), []).append(str(name))

    for row in _rows(conn, "sites"):
        raw_name = str(_value(row, "name", default="")).strip()
        if not raw_name:
            continue

        try:
            name = safe_site_name(raw_name)
        except PanelError as exc:
            report.add(Item("site", raw_name, "skip", str(exc)))
            continue

        if name in existing:
            report.add(Item("site", name, "skip", "already exists in SlimPanel"))
            continue

        conf_file = source.vhost_dir / f"{name}.conf"
        parsed = parse_vhost(conf_file.read_text(errors="replace")) if conf_file.is_file() else {}
        if not parsed:
            report.add(Item("site", name, "skip", f"vhost not found: {conf_file}"))
            continue

        db_path = str(_value(row, "path", default="") or "")
        conf_root = parsed["root"] or db_path
        run_path = ""
        if db_path and conf_root.startswith(db_path):
            run_path = conf_root[len(db_path) :].strip("/")

        domains = domains_by_site.get(int(_value(row, "id", default=0) or 0)) or parsed["domains"]
        site_type = site_type_of(parsed)

        report.add(
            Item(
                "site",
                name,
                "import",
                data={
                    "site_type": site_type.value,
                    "root": db_path or conf_root,
                    "run_path": run_path,
                    "index_files": parsed["index"] or "index.html index.htm",
                    "php_version": parsed["php_version"] if site_type == SiteType.php else "",
                    "proxy_target": parsed["proxy_target"],
                    "ssl": parsed["ssl"] and _cert_available(source, name),
                    "force_https": parsed["force_https"],
                    "domains": sorted(set(domains)) or [name],
                    "note": str(_value(row, "ps", default="") or ""),
                    "source_conf": str(conf_file),
                },
            )
        )
        existing.add(name)


def _cert_available(source: Source, name: str) -> bool:
    base = source.cert_dir / name
    return (base / "fullchain.pem").is_file() and (base / "privkey.pem").is_file()


def _plan_databases(session: Session, conn: sqlite3.Connection, report: Report) -> None:
    existing = {db.name for db in session.exec(select(Database)).all()}

    for row in _rows(conn, "databases"):
        raw_name = str(_value(row, "name", default="")).strip()
        if not raw_name:
            continue

        db_type = str(_value(row, "db_type", "type", default="") or "").lower()
        if db_type in {"mongodb", "pgsql", "postgresql", "sqlserver", "mssql", "redis"}:
            report.add(Item("database", raw_name, "skip", f"unsupported engine: {db_type}"))
            continue

        try:
            name = safe_identifier(raw_name)
        except PanelError as exc:
            report.add(Item("database", raw_name, "skip", str(exc)))
            continue

        if name in existing:
            report.add(Item("database", name, "skip", "already exists in SlimPanel"))
            continue

        report.add(
            Item(
                "database",
                name,
                "import",
                data={
                    "username": str(_value(row, "username", default=name) or name),
                    "password": str(_value(row, "password", default="") or ""),
                    "note": str(_value(row, "ps", default="") or ""),
                },
            )
        )
        existing.add(name)


def _plan_crons(
    session: Session, conn: sqlite3.Connection, source: Source, report: Report
) -> None:
    existing = {(job.name, job.schedule) for job in session.exec(select(CronJob)).all()}

    for row in _rows(conn, "crontab"):
        name = str(_value(row, "name", default="") or "").strip() or "imported job"
        echo = str(_value(row, "echo", default="") or "").strip()
        if not echo:
            report.add(Item("cron", name, "skip", "no script id"))
            continue

        script = source.cron_dir / echo
        if not script.is_file():
            report.add(Item("cron", name, "skip", f"script not found: {script}"))
            continue

        schedule = cron_schedule(row)
        if (name, schedule) in existing:
            report.add(Item("cron", name, "skip", "already exists in SlimPanel"))
            continue

        body = script.read_text(errors="replace")
        depends_on_aapanel = "/www/server/panel" in body
        enabled = bool(_value(row, "status", default=1)) and not depends_on_aapanel

        report.add(
            Item(
                "cron",
                name,
                "import",
                reason="disabled: script calls aaPanel internals" if depends_on_aapanel else "",
                data={
                    "schedule": schedule,
                    "script_source": str(script),
                    "enabled": enabled,
                },
            )
        )
        existing.add((name, schedule))


def apply(session: Session, source: Source, activate: bool = False) -> Report:
    report = plan(session, source)

    for item in report.of("site", "import"):
        _import_site(session, source, item, activate)
    for item in report.of("database", "import"):
        _import_database(session, item)
    for item in report.of("cron", "import"):
        _import_cron(session, item)

    from app.services import cron as cron_service

    if report.of("cron", "import"):
        cron_service.sync(session)
    return report


def _import_site(session: Session, source: Source, item: Item, activate: bool) -> None:
    data = item.data
    site = Site(
        name=item.name,
        site_type=SiteType(data["site_type"]),
        root=data["root"],
        run_path=data["run_path"],
        index_files=data["index_files"],
        php_version=data["php_version"],
        proxy_target=data["proxy_target"],
        ssl_enabled=data["ssl"],
        force_https=data["force_https"] and data["ssl"],
        enabled=activate,
        note=data["note"],
    )
    session.add(site)
    session.commit()

    for domain in data["domains"]:
        session.add(Domain(site_id=site.id, name=domain))
    session.commit()

    if data["ssl"]:
        _copy_cert(source, item.name)

    source_rewrite = source.rewrite_dir / f"{item.name}.conf"
    if source_rewrite.is_file():
        settings.ensure_dirs()
        nginx.rewrite_file(item.name).write_text(source_rewrite.read_text(errors="replace"))

    nginx.write_vhost(site, data["domains"])
    if not activate:
        nginx.set_enabled(item.name, False)

    item.reason = "imported" + ("" if activate else " (parked, not served yet)")


def _copy_cert(source: Source, name: str) -> None:
    target_cert, target_key = nginx.cert_paths(name)
    target_cert.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source.cert_dir / name / "fullchain.pem", target_cert)
    shutil.copyfile(source.cert_dir / name / "privkey.pem", target_key)
    target_key.chmod(0o600)


def _import_database(session: Session, item: Item) -> None:
    session.add(
        Database(
            name=item.name,
            username=item.data["username"],
            password=item.data["password"],
            note=item.data["note"],
        )
    )
    session.commit()
    item.reason = "registered (MySQL objects left untouched)"


def _import_cron(session: Session, item: Item) -> None:
    settings.ensure_dirs()
    scripts_dir = settings.data_dir / "cron-scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    source_script = Path(item.data["script_source"])
    target = scripts_dir / f"{source_script.name}.sh"
    shutil.copyfile(source_script, target)
    target.chmod(0o750)

    session.add(
        CronJob(
            name=item.name,
            schedule=item.data["schedule"],
            command=f"bash {target}",
            enabled=item.data["enabled"],
        )
    )
    session.commit()
    item.reason = item.reason or "imported"
