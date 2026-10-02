from __future__ import annotations

import shlex
from pathlib import Path

from sqlmodel import Session

from app.errors import PanelError
from app.models import SiteType, TaskRecord
from app.schemas import DatabaseCreate, SiteCreate
from app.services import mysql, rewrites, sites, tasks
from app.services.paths import safe_site_name

# One-click deployments, the equivalent of aaPanel's "one key WordPress".
APPS: dict[str, dict] = {
    "wordpress": {
        "label": "WordPress",
        "description": "The latest WordPress release, with its database and wp-config.php written for you.",
        "site_type": "php",
        "php_version": "8.1",
        "needs_database": True,
        "rewrite": "wordpress",
        "run_path": "",
        "archive": "https://wordpress.org/latest.tar.gz",
        "strip": "wordpress",
    },
    "laravel-skeleton": {
        "label": "Laravel skeleton",
        "description": "A minimal Laravel layout with public/ as the run path. Install vendor/ yourself.",
        "site_type": "php",
        "php_version": "8.2",
        "needs_database": True,
        "rewrite": "laravel",
        "run_path": "/public",
        "archive": "",
        "strip": "",
    },
    "static": {
        "label": "Static placeholder",
        "description": "A plain HTML site with a styled landing page.",
        "site_type": "static",
        "php_version": "",
        "needs_database": False,
        "rewrite": "none",
        "run_path": "",
        "archive": "",
        "strip": "",
    },
    "phpmyadmin": {
        "label": "phpMyAdmin",
        "description": "Database administration over the web. Protect it with directory auth.",
        "site_type": "php",
        "php_version": "8.1",
        "needs_database": False,
        "rewrite": "none",
        "run_path": "",
        "archive": "https://www.phpmyadmin.net/downloads/phpMyAdmin-latest-all-languages.tar.gz",
        "strip": "phpMyAdmin-*-all-languages",
    },
    "adminer": {
        "label": "Adminer",
        "description": "A single-file database client. Lighter than phpMyAdmin.",
        "site_type": "php",
        "php_version": "8.1",
        "needs_database": False,
        "rewrite": "none",
        "run_path": "",
        "archive": "",
        "strip": "",
        "single_file": ("index.php", "https://www.adminer.org/latest.php"),
    },
}

STATIC_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ margin:0; min-height:100vh; display:grid; place-items:center;
         font-family: ui-sans-serif, system-ui, sans-serif; background:#0f1117; color:#e6e8ee; }}
  .card {{ padding:40px 48px; border-radius:16px; background:#171a21; border:1px solid #262b35;
           text-align:center; max-width:32rem; }}
  h1 {{ margin:0 0 8px; font-size:1.6rem; }}
  p {{ margin:0; color:#9aa1b1; line-height:1.6; }}
  code {{ background:#20242e; padding:2px 6px; border-radius:4px; }}
</style>
</head>
<body>
  <div class="card">
    <h1>{name}</h1>
    <p>This site is live and served by SlimPanel.<br>Upload your files to <code>{root}</code>.</p>
  </div>
</body>
</html>
"""

WP_CONFIG = """<?php
define( 'DB_NAME', '{db_name}' );
define( 'DB_USER', '{db_user}' );
define( 'DB_PASSWORD', '{db_password}' );
define( 'DB_HOST', '{db_host}' );
define( 'DB_CHARSET', 'utf8mb4' );
define( 'DB_COLLATE', '' );

{salts}

$table_prefix = 'wp_';

define( 'WP_DEBUG', false );
define( 'DISALLOW_FILE_EDIT', true );
define( 'FS_METHOD', 'direct' );

if ( ! defined( 'ABSPATH' ) ) {{
	define( 'ABSPATH', __DIR__ . '/' );
}}

require_once ABSPATH . 'wp-settings.php';
"""

SALT_KEYS = [
    "AUTH_KEY", "SECURE_AUTH_KEY", "LOGGED_IN_KEY", "NONCE_KEY",
    "AUTH_SALT", "SECURE_AUTH_SALT", "LOGGED_IN_SALT", "NONCE_SALT",
]


def catalogue() -> list[dict]:
    return [
        {
            "key": key,
            "label": app["label"],
            "description": app["description"],
            "site_type": app["site_type"],
            "needs_database": app["needs_database"],
            "needs_download": bool(app["archive"] or app.get("single_file")),
        }
        for key, app in APPS.items()
    ]


def _salts() -> str:
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_[]{}<>~`+=,.;:/?|"
    lines = []
    for key in SALT_KEYS:
        value = "".join(secrets.choice(alphabet) for _ in range(64)).replace("'", "|")
        lines.append(f"define( '{key}', '{value}' );")
    return "\n".join(lines)


def deploy(
    session: Session,
    app_key: str,
    site_name: str,
    domains: list[str] | None = None,
    php_version: str = "",
) -> dict:
    """Create the site, the database and the files, then hand back a task id."""
    app = APPS.get(app_key)
    if not app:
        raise PanelError(f"Unknown application '{app_key}'")

    name = safe_site_name(site_name)
    site = sites.create_site(
        session,
        SiteCreate(
            name=name,
            site_type=SiteType(app["site_type"]),
            domains=domains or [name],
            php_version=php_version or app["php_version"],
            note=f"Deployed by SlimPanel ({app['label']})",
        ),
    )

    database = None
    if app["needs_database"]:
        db_name = ("sp_" + name.replace(".", "_").replace("-", "_"))[:60]
        database = mysql.create(session, DatabaseCreate(name=db_name, note=f"{app['label']} on {name}"))

    if app["rewrite"] != "none":
        try:
            from app.services import site_extras

            site_extras.write_rewrite(session, site.id, rewrites.get_template(app["rewrite"])["body"])
        except PanelError:
            pass

    if app["run_path"]:
        from app.schemas import SiteUpdate

        sites.update_site(session, site.id, SiteUpdate(run_path=app["run_path"]))

    root = Path(site.root)
    task: TaskRecord | None = None

    if app.get("single_file"):
        filename, url = app["single_file"]
        task = tasks.run_shell(
            session,
            f"Deploy {app['label']} to {name}",
            f"curl -fsSL {shlex.quote(url)} -o {shlex.quote(str(root / filename))}",
            timeout=600,
        )
    elif app["archive"]:
        strip = app["strip"]
        steps = [
            f"cd {shlex.quote(str(root))}",
            f"curl -fsSL {shlex.quote(app['archive'])} -o /tmp/{name}.tar.gz",
            f"tar -xzf /tmp/{name}.tar.gz -C /tmp/{name}_extract --one-top-level 2>/dev/null || "
            f"(mkdir -p /tmp/{name}_extract && tar -xzf /tmp/{name}.tar.gz -C /tmp/{name}_extract)",
            f"cp -rT \"$(find /tmp/{name}_extract -maxdepth 2 -type d -name '{strip or '*'}' | head -1)\" "
            f"{shlex.quote(str(root))} 2>/dev/null || cp -rT /tmp/{name}_extract {shlex.quote(str(root))}",
            f"rm -rf /tmp/{name}.tar.gz /tmp/{name}_extract",
            f"chown -R www-data:www-data {shlex.quote(str(root))} 2>/dev/null || true",
            f"find {shlex.quote(str(root))} -type d -exec chmod 755 {{}} +",
            f"find {shlex.quote(str(root))} -type f -exec chmod 644 {{}} +",
        ]
        command = " && ".join(steps)

        if app_key == "wordpress" and database:
            from app.config import settings

            config = WP_CONFIG.format(
                db_name=database.name,
                db_user=database.username,
                db_password=database.password,
                db_host=f"{settings.mysql_host}:{settings.mysql_port}",
                salts=_salts(),
            )
            config_path = root / "wp-config.php"
            config_path.write_text(config)
            config_path.chmod(0o640)
            command += f" && chmod 640 {shlex.quote(str(config_path))}"

        task = tasks.run_shell(session, f"Deploy {app['label']} to {name}", command, timeout=1800)
    else:
        index = root / "index.html"
        if app_key == "static" or not any(root.iterdir()):
            index.write_text(STATIC_PAGE.format(name=name, root=root))
        if app_key == "laravel-skeleton":
            (root / "public").mkdir(exist_ok=True)
            (root / "public" / "index.php").write_text(
                "<?php\n// Replace with Laravel's public/index.php after composer install.\n"
                "phpinfo();\n"
            )

    return {
        "site": site.model_dump(),
        "database": database.model_dump() if database else None,
        "task_id": task.id if task else None,
        "url": f"http://{(domains or [name])[0]}",
    }
