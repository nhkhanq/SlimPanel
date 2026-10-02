# SlimPanel

A small Linux hosting control panel: nginx sites, Let's Encrypt, MySQL, a file
manager, cron, backups and a web terminal. Roughly the useful 10% of a full
panel, written as a plain FastAPI app you can read in an afternoon.

No plugin store, no license server, no cloud calls.

## Features

| Area | What it does |
|---|---|
| Sites | static / PHP-FPM / reverse-proxy vhosts, domains, run path, index files, enable-disable, generated nginx config with `nginx -t` validation and rollback |
| SSL | Let's Encrypt via certbot webroot, custom certificate upload, force HTTPS, renew |
| Databases | MySQL create / drop / reset password / dump / import, per-database user and grants |
| Files | browse, read, edit, upload, download, move, copy, chmod, zip, unzip, tail — restricted to configured roots |
| System | CPU / memory / disk / load / network, process list and kill, systemd service control |
| Cron | jobs stored in SQLite and rendered into a dedicated `/etc/cron.d/slimpanel` file, run-now, per-job logs |
| Backups | site tarballs and database dumps, download, prune |
| Auth | session cookie, scrypt password hashing, TOTP two-factor, login and operation audit logs, optional secret entry path |
| Terminal | WebSocket PTY shell |

## Requirements

- Linux with nginx
- Python 3.10+
- Optional: MySQL/MariaDB client, `certbot`

## Install

```bash
git clone https://github.com/nhkhanq/SlimPanel.git /www/SlimPanel
cd /www/SlimPanel
bash deploy/install.sh
```

Then add one line inside the `http { }` block of your `nginx.conf`:

```nginx
include /www/SlimPanel/data/vhost/nginx/*.conf;
```

```bash
nginx -t && nginx -s reload
```

Start it:

```bash
.venv/bin/python runserver.py          # http://<server>:8899
```

The first start creates an `admin` account and writes the generated password to
`data/initial_credentials.txt`. Set `SLIMPANEL_ADMIN_PASSWORD` to choose your own.

## Configuration

`slimpanel.json` in the project root, or `SLIMPANEL_<FIELD>` environment
variables, which win over the file. Copy `slimpanel.example.json` to start.

| Key | Default | Notes |
|---|---|---|
| `port` | `8899` | panel listen port |
| `entry_path` | `""` | serve everything under a secret prefix, e.g. `"/x7kq"` |
| `data_dir` | `./data` | database, vhosts, certs, backups |
| `www_root` | `/www/wwwroot` | where new site roots are created |
| `file_roots` | `["/www/wwwroot", "/www/wwwlogs"]` | the only paths the file manager may touch |
| `managed_services` | `["nginx","mysql","redis"]` | the only services the panel may control |
| `php_fpm_socket` | `unix:/run/php/php{version}-fpm.sock` | `{version}` comes from the site |
| `cron_target` | `/etc/cron.d/slimpanel` | written additively, never touches existing crontabs |
| `dry_run` | `false` | log shell commands instead of running them |

SlimPanel writes its vhosts to its own directory and its cron entries to its own
`cron.d` file, so it can be installed next to an existing panel without touching
that panel's configuration.

## Layout

```
app/
  api/        HTTP routes, one module per area
  services/   the actual work: nginx, acme, mysql, files, system, cron, backup
  templates/  nginx vhost Jinja2 template
  static/     single-page UI, no build step
tests/        92 tests, all offline
deploy/       systemd unit and installer
```

Adding a feature is three files: a function in `app/services/`, a route in
`app/api/`, a view entry in `app/static/app.js`.

## Tests

```bash
.venv/bin/python -m pytest
```

Tests run against a temporary data directory with `dry_run` enabled, so they
never call nginx, systemd, certbot or MySQL.

## Security notes

The panel runs as root because it edits nginx config and controls services.

- Every file-manager path is resolved with `realpath` and must land inside
  `file_roots`; symlink escapes and `..` are rejected.
- Site names and database identifiers are validated against an allowlist.
- Cron commands may not contain newlines or `%`.
- Only services listed in `managed_services` can be started or stopped.
- Put the panel behind a firewall rule, set `entry_path`, and enable TOTP.

## License

MIT
