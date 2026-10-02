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
| Import | read an existing aaPanel install and bring over its sites, domains, certificates, rewrite rules, databases and cron jobs |

## Requirements

- Linux with nginx
- Python 3.10+
- Optional: MySQL/MariaDB client, `certbot`

## Install

One command. It installs the dependencies, clones the repo, builds the
virtualenv, writes the config, wires up nginx, installs the systemd unit,
starts the service and prints your login:

```bash
curl -fsSL https://raw.githubusercontent.com/nhkhanq/SlimPanel/main/install.sh | sudo bash
```

Knobs, all optional:

```bash
curl -fsSL .../install.sh | sudo SLIMPANEL_PORT=9000 SLIMPANEL_DIR=/opt/slimpanel bash
```

| Variable | Default | Effect |
|---|---|---|
| `SLIMPANEL_PORT` | `8899` | panel port |
| `SLIMPANEL_DIR` | `/www/SlimPanel` | install location |
| `SLIMPANEL_BRANCH` | `main` | branch to install |
| `SLIMPANEL_SKIP_NGINX` | `0` | do not touch nginx |
| `SLIMPANEL_SKIP_SERVICE` | `0` | do not install the systemd unit |

The installer only adds an nginx include when it finds a drop-in directory it
can write to; otherwise it prints the one line for you to paste. It never edits
an existing `nginx.conf`.

Re-running the installer upgrades in place. To remove the service and the nginx
include while keeping your data:

```bash
sudo bash /www/SlimPanel/uninstall.sh
```

### Manual install

```bash
git clone https://github.com/nhkhanq/SlimPanel.git /www/SlimPanel
cd /www/SlimPanel && make install && make run
```

The first start creates an `admin` account and writes the generated password to
`data/initial_credentials.txt`. Set `SLIMPANEL_ADMIN_PASSWORD` to choose your own.

## Importing from aaPanel

SlimPanel can read an existing aaPanel installation and take over its sites.
Nothing is written until you pass `--apply`, and aaPanel itself is only ever
read.

```bash
.venv/bin/python -m app.cli inspect-aapanel        # show the aaPanel schema
.venv/bin/python -m app.cli import-aapanel         # dry run, prints a plan
.venv/bin/python -m app.cli import-aapanel --apply # write it
```

The same thing lives under **Import** in the web UI.

What comes across:

| From aaPanel | Into SlimPanel |
|---|---|
| `sites` + `domain` tables | sites and their domains |
| each site's vhost file | type (static / PHP / proxy), PHP version, run path, index files, SSL and force-HTTPS flags, proxy target |
| `vhost/cert/<site>/` | certificates, copied into SlimPanel's cert directory |
| `vhost/rewrite/<site>.conf` | rewrite rules |
| `databases` table | database records with their credentials — the MySQL databases themselves are left alone, and records whose database no longer exists are skipped as stale |
| `crontab` table | cron jobs, with aaPanel's schedule model converted to standard cron syntax and the shell script copied into SlimPanel |

The vhost parser follows `include` directives inside the aaPanel directory, so
reverse proxies that aaPanel keeps in `vhost/nginx/proxy/<site>/` are found
rather than read as static sites. A proxy on `location /` becomes a proxy site;
proxies on other locations are copied verbatim into the site's extra config and
listed in the report. A document root that points outside the recorded site
path is kept as-is instead of being mistaken for a run path.

When SlimPanel can reach MySQL it checks each recorded database actually
exists; panels that have been running for a while accumulate records for
databases that were dropped outside the panel. `inspect-aapanel` also reports
whether aaPanel has a MySQL root password on file, so you know whether that
check can run — copy it into `mysql_password` in `slimpanel.json` first.

What is skipped, and why it tells you so: sites with no vhost file, names that
fail validation, non-MySQL engines (MongoDB, PostgreSQL, SQL Server, Redis),
stale database records, and cron jobs whose script is missing. Cron jobs whose script calls aaPanel
internals are imported but left disabled, because they break once aaPanel is
gone.

**Imported sites are parked.** Their vhosts are written as `*.conf.disabled` so
nginx keeps serving aaPanel's copies and no `server_name` conflicts appear. The
cutover is yours to make:

1. `import-aapanel --apply`, then check each site under **Sites**
2. remove aaPanel's include from `nginx.conf`
3. add SlimPanel's include
4. start the sites in SlimPanel, or re-run the import with `--activate`
5. `nginx -t && nginx -s reload`

Roll back by reversing steps 2 and 3 — aaPanel's own vhost files are never
modified.

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
| `nginx_bin` | `auto` | detected from the running nginx, then `$PATH`; set it explicitly if you run several |
| `cron_target` | `/etc/cron.d/slimpanel` | written additively, never touches existing crontabs |
| `dry_run` | `false` | log shell commands instead of running them |

SlimPanel writes its vhosts to its own directory and its cron entries to its own
`cron.d` file, so it can be installed next to an existing panel without touching
that panel's configuration.

The panel finds nginx by looking at the running master process first, so on a
host where another panel ships its own build (aaPanel puts 1.24 in
`/www/server/nginx/sbin/nginx` while Ubuntu's 1.18 sits in `/usr/sbin`) it tests
and reloads the one actually serving your sites. The generated vhost follows
that binary's version too: HTTP/2 is written as a `listen` flag below nginx
1.25.1 and as its own `http2 on;` directive from 1.25.1 up.

## Layout

```
app/
  api/           HTTP routes, one module per area
  cli.py         serve, import-aapanel, inspect-aapanel, create-user, set-password
  services/      the actual work: nginx, acme, mysql, files, system, cron, backup
  templates/     nginx vhost Jinja2 template
  static/dist/   the built web interface, committed so installs need no Node
web/
  src/views/     one Vue file per page
  src/components/ stat cards and the usage chart
tests/           150 tests, all offline
deploy/          systemd unit and service file
```

Adding a feature is three files: a function in `app/services/`, a route in
`app/api/`, a view in `web/src/views/`.

## Web interface

Vue 3 + Vite + [Naive UI](https://www.naiveui.com/), hash-routed, served by the
panel itself from `app/static/dist`. Dark and light themes, ~1.3 MB of built
assets.

The build output is committed, so installing the panel needs no Node. You only
need Node to change the interface:

```bash
cd web
npm install
npm run dev      # http://localhost:5173, proxies /api to the panel on :8899
npm run build    # writes app/static/dist
```

Commit `app/static/dist` with your change — the server has no build step.

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
