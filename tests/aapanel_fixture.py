from __future__ import annotations

import sqlite3
from pathlib import Path

PHP_CONF = """server
{{
    listen 80;
    listen 443 ssl http2 ;
    server_name php.test www.php.test;
    index index.php index.html;
    root /www/wwwroot/php.test/public;

    #CERT-APPLY-CHECK--START
    #include /www/server/panel/vhost/nginx/well-known/php.test.conf;
    #CERT-APPLY-CHECK--END
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){{
        rewrite ^(/.*)$ https://$host$1 permanent;
    }}
    #HTTP_TO_HTTPS_END
    ssl_certificate    /www/server/panel/vhost/cert/php.test/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/php.test/privkey.pem;

    #PHP-INFO-START
    include enable-php-74.conf;
    #PHP-INFO-END

    include /www/server/panel/vhost/rewrite/php.test.conf;
    access_log  /www/wwwlogs/php.test.log;
}}
"""

PROXY_CONF = """server
{
    listen 80;
    server_name proxy.test;
    index index.html;
    root /www/wwwroot/proxy.test;

    location /
    {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }
    access_log  /www/wwwlogs/proxy.test.log;
}
"""

STATIC_CONF = """server
{
    listen 80;
    server_name static.test;
    index index.html index.htm;
    root /www/wwwroot/static.test;
    #ssl_certificate /www/server/panel/vhost/cert/static.test/fullchain.pem;
    access_log  /www/wwwlogs/static.test.log;
}
"""

NODE_CONF = """server
{
    listen 80;
    server_name node.test;
    index index.html;
    root /www/wwwroot/node.test;
    include /PANEL/vhost/nginx/proxy/node.test/*.conf;
    access_log  /www/wwwlogs/node.test.log;
}
"""

NODE_PROXY_INCLUDE = """location /
{
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
}
"""

MOVED_CONF = """server
{
    listen 80;
    server_name moved.test;
    index index.html;
    root /srv/app/dist;
    access_log  /www/wwwlogs/moved.test.log;
}
"""

SPA_CONF = """server
{
    listen 80;
    listen 443 ssl http2 ;
    server_name spa.test;
    index index.html;
    root /www/wwwroot/spa.test;
    ssl_certificate    /PANEL/vhost/cert/spa.test/fullchain.pem;
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END
    include /PANEL/vhost/rewrite/spa.test.conf;
    access_log  /www/wwwlogs/spa.test.log;
}
"""

SPA_REWRITE = """location /
{
    try_files $uri $uri/ /index.html;
}
"""

MIXED_CONF = """server
{
    listen 80;
    server_name mixed.test;
    index index.html;
    root /www/wwwroot/mixed.test;

    location ~ ^/(api|auth)(/|$)
    {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
    }
    access_log  /www/wwwlogs/mixed.test.log;
}
"""

PLAIN_SCRIPT = "#!/bin/bash\necho nightly backup\n"
PANEL_SCRIPT = "#!/bin/bash\n/www/server/panel/pyenv/bin/python /www/server/panel/script/backup.py site\n"

SCHEMA = """
CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, path TEXT, status TEXT, ps TEXT,
    "index" TEXT, addtime TEXT, edate TEXT, type_id INTEGER, project_type TEXT
);
CREATE TABLE domain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid INTEGER, name TEXT, port INTEGER, addtime TEXT
);
CREATE TABLE databases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, username TEXT, password TEXT, accept TEXT, ps TEXT,
    addtime TEXT, pid INTEGER, type TEXT, db_type TEXT
);
CREATE TABLE crontab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, type TEXT, where1 TEXT, where_hour INTEGER, where_minute INTEGER,
    echo TEXT, addtime TEXT, status INTEGER, save TEXT, backupTo TEXT, sType TEXT
);
CREATE TABLE ftps (id INTEGER PRIMARY KEY AUTOINCREMENT, pid INTEGER, name TEXT);
CREATE TABLE config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webserver TEXT, backup_path TEXT, sites_path TEXT, status INTEGER, mysql_root TEXT
);
"""


def build(base: Path) -> tuple[Path, Path]:
    panel_dir = base / "server" / "panel"
    cron_dir = base / "server" / "cron"
    for sub in ("data", "vhost/nginx", "vhost/cert", "vhost/rewrite"):
        (panel_dir / sub).mkdir(parents=True, exist_ok=True)
    cron_dir.mkdir(parents=True, exist_ok=True)

    vhosts = panel_dir / "vhost" / "nginx"
    (vhosts / "php.test.conf").write_text(PHP_CONF.format())
    (vhosts / "proxy.test.conf").write_text(PROXY_CONF)
    (vhosts / "static.test.conf").write_text(STATIC_CONF)
    (vhosts / "node.test.conf").write_text(NODE_CONF.replace("/PANEL", str(panel_dir)))
    (vhosts / "moved.test.conf").write_text(MOVED_CONF)
    (vhosts / "spa.test.conf").write_text(SPA_CONF.replace("/PANEL", str(panel_dir)))
    (vhosts / "mixed.test.conf").write_text(MIXED_CONF)

    proxy_include = vhosts / "proxy" / "node.test"
    proxy_include.mkdir(parents=True, exist_ok=True)
    (proxy_include / "node.test.conf").write_text(NODE_PROXY_INCLUDE)

    cert = panel_dir / "vhost" / "cert" / "php.test"
    cert.mkdir(parents=True, exist_ok=True)
    (cert / "fullchain.pem").write_text("FULLCHAIN")
    (cert / "privkey.pem").write_text("PRIVKEY")

    (panel_dir / "vhost" / "rewrite" / "php.test.conf").write_text("location /old { return 301 /new; }\n")
    (panel_dir / "vhost" / "rewrite" / "spa.test.conf").write_text(SPA_REWRITE)

    spa_cert = panel_dir / "vhost" / "cert" / "spa.test"
    spa_cert.mkdir(parents=True, exist_ok=True)
    (spa_cert / "fullchain.pem").write_text("SPA-FULLCHAIN")
    (spa_cert / "privkey.pem").write_text("SPA-PRIVKEY")

    (cron_dir / "aaaa1111").write_text(PLAIN_SCRIPT)
    (cron_dir / "bbbb2222").write_text(PANEL_SCRIPT)

    db_path = panel_dir / "data" / "default.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.executemany(
        'INSERT INTO sites (id, name, path, status, ps, "index") VALUES (?, ?, ?, ?, ?, ?)',
        [
            (1, "php.test", "/www/wwwroot/php.test", "1", "php site", "index.php"),
            (2, "proxy.test", "/www/wwwroot/proxy.test", "1", "node app", "index.html"),
            (3, "static.test", "/www/wwwroot/static.test", "1", "", "index.html"),
            (4, "missing.test", "/www/wwwroot/missing.test", "1", "", "index.html"),
            (5, "Bad Name", "/www/wwwroot/bad", "1", "", "index.html"),
            (6, "node.test", "/www/wwwroot/node.test", "1", "node app", "index.html"),
            (7, "moved.test", "/www/wwwroot/moved.test", "1", "moved root", "index.html"),
            (8, "spa.test", "/www/wwwroot/spa.test", "1", "single page app", "index.html"),
            (9, "mixed.test", "/www/wwwroot/mixed.test", "1", "static plus api", "index.html"),
        ],
    )
    conn.executemany(
        "INSERT INTO domain (pid, name, port) VALUES (?, ?, ?)",
        [
            (1, "php.test", 80),
            (1, "www.php.test", 80),
            (2, "proxy.test", 80),
            (3, "static.test", 80),
            (6, "node.test", 80),
            (7, "moved.test", 80),
            (8, "spa.test", 80),
            (9, "mixed.test", 80),
        ],
    )
    conn.executemany(
        "INSERT INTO databases (name, username, password, ps, db_type) VALUES (?, ?, ?, ?, ?)",
        [
            ("app_db", "app_db", "s3cret", "main database", "MySQL"),
            ("logs_db", "logs_user", "pw2", "", ""),
            ("mongo_db", "mongo_user", "pw3", "", "mongodb"),
            ("bad-name", "x", "y", "", ""),
        ],
    )
    conn.executemany(
        "INSERT INTO crontab (name, type, where1, where_hour, where_minute, echo, status)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("nightly log rotate", "day", "", 3, 30, "aaaa1111", 1),
            ("aapanel site backup", "week", "1", 2, 0, "bbbb2222", 1),
            ("broken job", "day", "", 1, 0, "missing-script", 1),
            ("every 5 minutes", "minute-n", "5", 0, 0, "aaaa1111", 1),
        ],
    )
    conn.execute(
        "INSERT INTO config (webserver, backup_path, sites_path, status, mysql_root)"
        " VALUES (?, ?, ?, ?, ?)",
        ("nginx", "/www/backup", "/www/wwwroot", 1, "root-secret"),
    )
    conn.commit()
    conn.close()
    return panel_dir, cron_dir
