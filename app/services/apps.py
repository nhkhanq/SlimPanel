from __future__ import annotations

import re
import shutil
from pathlib import Path

from sqlmodel import Session

from app.config import settings
from app.errors import PanelError
from app.models import TaskRecord
from app.services import shell, tasks

VERSION_PATTERN = re.compile(r"(\d+\.\d+(?:\.\d+)?)")


def package_manager() -> str:
    for manager in ("apt-get", "dnf", "yum", "zypper", "pacman", "apk"):
        if shutil.which(manager):
            return manager
    return ""


def _install_command(manager: str, package: str) -> str:
    return {
        "apt-get": f"DEBIAN_FRONTEND=noninteractive apt-get install -y {package}",
        "dnf": f"dnf install -y {package}",
        "yum": f"yum install -y {package}",
        "zypper": f"zypper --non-interactive install {package}",
        "pacman": f"pacman -S --noconfirm {package}",
        "apk": f"apk add --no-cache {package}",
    }[manager]


def _remove_command(manager: str, package: str) -> str:
    return {
        "apt-get": f"DEBIAN_FRONTEND=noninteractive apt-get remove -y {package}",
        "dnf": f"dnf remove -y {package}",
        "yum": f"yum remove -y {package}",
        "zypper": f"zypper --non-interactive remove {package}",
        "pacman": f"pacman -R --noconfirm {package}",
        "apk": f"apk del {package}",
    }[manager]


# The catalogue aaPanel calls the App Store, with the package name per family.
CATALOGUE: list[dict] = [
    {
        "slug": "nginx",
        "name": "Nginx",
        "category": "web",
        "description": "HTTP server and reverse proxy. The one SlimPanel writes vhosts for.",
        "probe": "nginx",
        "version_cmd": "nginx -v",
        "service": "nginx",
        "packages": {"apt-get": "nginx", "dnf": "nginx", "yum": "nginx", "apk": "nginx", "pacman": "nginx", "zypper": "nginx"},
    },
    {
        "slug": "apache",
        "name": "Apache",
        "category": "web",
        "description": "Alternative web server, usually behind nginx as a PHP handler.",
        "probe": "apache2ctl",
        "version_cmd": "apache2ctl -v",
        "service": "apache2",
        "packages": {"apt-get": "apache2", "dnf": "httpd", "yum": "httpd", "apk": "apache2", "pacman": "apache", "zypper": "apache2"},
    },
    {
        "slug": "mysql",
        "name": "MySQL / MariaDB",
        "category": "database",
        "description": "Relational database. Powers the Databases page.",
        "probe": "mysql",
        "version_cmd": "mysql --version",
        "service": "mysql",
        "packages": {"apt-get": "mariadb-server mariadb-client", "dnf": "mariadb-server", "yum": "mariadb-server", "apk": "mariadb mariadb-client", "pacman": "mariadb", "zypper": "mariadb"},
    },
    {
        "slug": "postgresql",
        "name": "PostgreSQL",
        "category": "database",
        "description": "Relational database with its own page under Databases.",
        "probe": "psql",
        "version_cmd": "psql --version",
        "service": "postgresql",
        "packages": {"apt-get": "postgresql postgresql-client", "dnf": "postgresql-server", "yum": "postgresql-server", "apk": "postgresql", "pacman": "postgresql", "zypper": "postgresql-server"},
    },
    {
        "slug": "redis",
        "name": "Redis",
        "category": "database",
        "description": "In-memory key/value store, also used as a PHP session backend.",
        "probe": "redis-server",
        "version_cmd": "redis-server --version",
        "service": "redis-server",
        "packages": {"apt-get": "redis-server", "dnf": "redis", "yum": "redis", "apk": "redis", "pacman": "redis", "zypper": "redis"},
    },
    {
        "slug": "memcached",
        "name": "Memcached",
        "category": "database",
        "description": "Memory object cache.",
        "probe": "memcached",
        "version_cmd": "memcached --version",
        "service": "memcached",
        "packages": {"apt-get": "memcached", "dnf": "memcached", "yum": "memcached", "apk": "memcached", "pacman": "memcached", "zypper": "memcached"},
    },
    {
        "slug": "mongodb",
        "name": "MongoDB",
        "category": "database",
        "description": "Document database.",
        "probe": "mongod",
        "version_cmd": "mongod --version",
        "service": "mongod",
        "packages": {"apt-get": "mongodb-org", "dnf": "mongodb-org", "yum": "mongodb-org", "apk": "mongodb", "pacman": "mongodb", "zypper": "mongodb"},
    },
    {
        "slug": "php",
        "name": "PHP-FPM",
        "category": "runtime",
        "description": "PHP FastCGI process manager. Versions are managed on the PHP page.",
        "probe": "php",
        "version_cmd": "php -v",
        "service": "",
        "packages": {"apt-get": "php-fpm php-cli php-mysql php-curl php-gd php-mbstring php-xml php-zip", "dnf": "php-fpm php-cli php-mysqlnd", "yum": "php-fpm php-cli php-mysqlnd", "apk": "php php-fpm", "pacman": "php php-fpm", "zypper": "php php-fpm"},
    },
    {
        "slug": "nodejs",
        "name": "Node.js",
        "category": "runtime",
        "description": "JavaScript runtime for Node projects.",
        "probe": "node",
        "version_cmd": "node -v",
        "service": "",
        "packages": {"apt-get": "nodejs npm", "dnf": "nodejs npm", "yum": "nodejs npm", "apk": "nodejs npm", "pacman": "nodejs npm", "zypper": "nodejs npm"},
    },
    {
        "slug": "python",
        "name": "Python 3",
        "category": "runtime",
        "description": "Python runtime and venv support for Python projects.",
        "probe": "python3",
        "version_cmd": "python3 -V",
        "service": "",
        "packages": {"apt-get": "python3 python3-venv python3-pip", "dnf": "python3 python3-pip", "yum": "python3 python3-pip", "apk": "python3 py3-pip", "pacman": "python python-pip", "zypper": "python3 python3-pip"},
    },
    {
        "slug": "java",
        "name": "Java (OpenJDK)",
        "category": "runtime",
        "description": "JDK for Java projects and Tomcat.",
        "probe": "java",
        "version_cmd": "java -version",
        "service": "",
        "packages": {"apt-get": "default-jdk", "dnf": "java-latest-openjdk", "yum": "java-11-openjdk", "apk": "openjdk17", "pacman": "jdk-openjdk", "zypper": "java-11-openjdk"},
    },
    {
        "slug": "golang",
        "name": "Go",
        "category": "runtime",
        "description": "Go toolchain for Go projects.",
        "probe": "go",
        "version_cmd": "go version",
        "service": "",
        "packages": {"apt-get": "golang-go", "dnf": "golang", "yum": "golang", "apk": "go", "pacman": "go", "zypper": "go"},
    },
    {
        "slug": "docker",
        "name": "Docker",
        "category": "container",
        "description": "Container engine. Powers the Docker page.",
        "probe": "docker",
        "version_cmd": "docker --version",
        "service": "docker",
        "packages": {"apt-get": "docker.io docker-compose-plugin", "dnf": "docker", "yum": "docker", "apk": "docker docker-cli-compose", "pacman": "docker docker-compose", "zypper": "docker"},
    },
    {
        "slug": "certbot",
        "name": "Certbot",
        "category": "tool",
        "description": "Let's Encrypt client used to issue site certificates.",
        "probe": "certbot",
        "version_cmd": "certbot --version",
        "service": "",
        "packages": {"apt-get": "certbot", "dnf": "certbot", "yum": "certbot", "apk": "certbot", "pacman": "certbot", "zypper": "certbot"},
    },
    {
        "slug": "pure-ftpd",
        "name": "Pure-FTPd",
        "category": "tool",
        "description": "FTP server behind the FTP page.",
        "probe": "pure-ftpd",
        "version_cmd": "pure-ftpd --help",
        "service": "pure-ftpd",
        "packages": {"apt-get": "pure-ftpd", "dnf": "pure-ftpd", "yum": "pure-ftpd", "apk": "pure-ftpd", "pacman": "pure-ftpd", "zypper": "pure-ftpd"},
    },
    {
        "slug": "supervisor",
        "name": "Supervisor",
        "category": "tool",
        "description": "Process manager. SlimPanel's own projects use systemd instead.",
        "probe": "supervisord",
        "version_cmd": "supervisord --version",
        "service": "supervisor",
        "packages": {"apt-get": "supervisor", "dnf": "supervisor", "yum": "supervisor", "apk": "supervisor", "pacman": "supervisor", "zypper": "supervisor"},
    },
    {
        "slug": "fail2ban",
        "name": "Fail2ban",
        "category": "security",
        "description": "Bans IPs that fail authentication repeatedly.",
        "probe": "fail2ban-server",
        "version_cmd": "fail2ban-server --version",
        "service": "fail2ban",
        "packages": {"apt-get": "fail2ban", "dnf": "fail2ban", "yum": "fail2ban", "apk": "fail2ban", "pacman": "fail2ban", "zypper": "fail2ban"},
    },
    {
        "slug": "git",
        "name": "Git",
        "category": "tool",
        "description": "Needed to deploy sites and projects from a repository.",
        "probe": "git",
        "version_cmd": "git --version",
        "service": "",
        "packages": {"apt-get": "git", "dnf": "git", "yum": "git", "apk": "git", "pacman": "git", "zypper": "git"},
    },
    {
        "slug": "unzip",
        "name": "Unzip / Tar tools",
        "category": "tool",
        "description": "Archive handling for the file manager.",
        "probe": "unzip",
        "version_cmd": "unzip -v",
        "service": "",
        "packages": {"apt-get": "unzip zip tar", "dnf": "unzip zip tar", "yum": "unzip zip tar", "apk": "unzip zip tar", "pacman": "unzip zip tar", "zypper": "unzip zip tar"},
    },
]

BY_SLUG = {item["slug"]: item for item in CATALOGUE}


def _version_of(app: dict) -> str:
    if not shutil.which(app["probe"]):
        return ""
    result = shell.run(app["version_cmd"], timeout=15)
    match = VERSION_PATTERN.search(result.output)
    return match.group(1) if match else "installed"


def _state_of(service: str) -> str:
    if not service:
        return ""
    result = shell.run([settings.systemctl_bin, "is-active", service], timeout=10)
    return result.stdout.strip() or result.stderr.strip() or "unknown"


def catalogue() -> list[dict]:
    manager = package_manager()
    rows = []
    for app in CATALOGUE:
        installed = bool(shutil.which(app["probe"]))
        rows.append(
            {
                "slug": app["slug"],
                "name": app["name"],
                "category": app["category"],
                "description": app["description"],
                "installed": installed,
                "version": _version_of(app) if installed else "",
                "service": app["service"],
                "state": _state_of(app["service"]) if installed else "",
                "package": app["packages"].get(manager, ""),
                "installable": bool(manager and app["packages"].get(manager)),
            }
        )
    return rows


def get(slug: str) -> dict:
    app = BY_SLUG.get(slug)
    if not app:
        raise PanelError(f"Unknown app '{slug}'")
    return app


def install(session: Session, slug: str) -> TaskRecord:
    app = get(slug)
    manager = package_manager()
    if not manager:
        raise PanelError("No supported package manager found on this host")
    package = app["packages"].get(manager)
    if not package:
        raise PanelError(f"{app['name']} has no package for {manager}")

    refresh = {"apt-get": "apt-get update -y && ", "apk": "apk update && "}.get(manager, "")
    command = refresh + _install_command(manager, package)
    return tasks.run_shell(session, f"Install {app['name']}", command, timeout=1800)


def uninstall(session: Session, slug: str) -> TaskRecord:
    app = get(slug)
    manager = package_manager()
    if not manager:
        raise PanelError("No supported package manager found on this host")
    package = app["packages"].get(manager)
    if not package:
        raise PanelError(f"{app['name']} has no package for {manager}")
    return tasks.run_shell(
        session, f"Remove {app['name']}", _remove_command(manager, package), timeout=1800
    )


def system_update(session: Session) -> TaskRecord:
    manager = package_manager()
    command = {
        "apt-get": "apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
        "dnf": "dnf upgrade -y",
        "yum": "yum update -y",
        "zypper": "zypper --non-interactive update",
        "pacman": "pacman -Syu --noconfirm",
        "apk": "apk update && apk upgrade",
    }.get(manager)
    if not command:
        raise PanelError("No supported package manager found on this host")
    return tasks.run_shell(session, "System update", command, timeout=3600)


def upgradable() -> list[dict]:
    manager = package_manager()
    if manager == "apt-get":
        result = shell.run("apt list --upgradable 2>/dev/null", timeout=60)
        rows = []
        for line in result.stdout.splitlines():
            if "/" not in line or "upgradable from" not in line:
                continue
            name = line.split("/", 1)[0]
            parts = line.split()
            rows.append({"name": name, "candidate": parts[1] if len(parts) > 1 else ""})
        return rows
    if manager in {"dnf", "yum"}:
        result = shell.run(f"{manager} check-update -q", timeout=120)
        rows = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3 and not line.startswith(" "):
                rows.append({"name": parts[0], "candidate": parts[1]})
        return rows
    return []


def config_files(slug: str) -> list[dict]:
    """The config files a panel offers to edit for each service."""
    known = {
        "nginx": ["/etc/nginx/nginx.conf", "/www/server/nginx/conf/nginx.conf"],
        "apache": ["/etc/apache2/apache2.conf", "/etc/httpd/conf/httpd.conf"],
        "mysql": ["/etc/mysql/my.cnf", "/etc/my.cnf", "/www/server/mysql/etc/my.cnf"],
        "postgresql": ["/etc/postgresql/postgresql.conf", "/var/lib/pgsql/data/postgresql.conf"],
        "redis": ["/etc/redis/redis.conf", "/www/server/redis/redis.conf"],
        "memcached": ["/etc/memcached.conf"],
        "mongodb": ["/etc/mongod.conf"],
        "supervisor": ["/etc/supervisor/supervisord.conf"],
        "fail2ban": ["/etc/fail2ban/jail.local", "/etc/fail2ban/jail.conf"],
        "pure-ftpd": ["/etc/pure-ftpd/pure-ftpd.conf", "/www/server/pure-ftpd/etc/pure-ftpd.conf"],
        "docker": ["/etc/docker/daemon.json"],
    }
    return [{"path": path, "exists": Path(path).is_file()} for path in known.get(slug, [])]
