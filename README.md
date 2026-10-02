# SlimPanel

A Linux hosting control panel: websites, SSL, databases, app projects, FTP, a
file manager, Docker, firewall and SSH management, monitoring, backups, alerts
and a web terminal — the feature set of aaPanel, written as a plain FastAPI app
you can read.

No plugin store, no license server, no cloud calls, no telemetry.

![25 API areas, 300 endpoints, 417 offline tests](https://img.shields.io/badge/API-300%20endpoints-20a53a) ![tests](https://img.shields.io/badge/tests-417%20offline-20a53a)

## Features

| Area | What it does |
|---|---|
| **Websites** | static / PHP / reverse-proxy / load-balanced / Node / Python / Java / Go / .NET vhosts, site groups, multiple domains, run path, index files, start-stop, generated nginx config with `nginx -t` validation and rollback |
| **Per-site controls** | pseudo-static library (20 templates incl. WordPress, Laravel, ThinkPHP, Discuz), 301/302 redirects by path or domain, extra reverse proxies with caching and content replacement, directory passwords, hotlink protection, blocked extensions, rate and connection limits, IP allow/deny, gzip, static cache, custom headers, a lightweight request filter |
| **SSL** | Let's Encrypt via certbot webroot, custom certificate upload, force HTTPS, HSTS, TLS protocol choice, renew, expiry tracking |
| **Databases** | MySQL/MariaDB create / drop / reset password / dump / import with per-database users; PostgreSQL databases and roles; MongoDB listing and stats; Redis info, config, key browser and flush; extra local or remote servers with a connection test |
| **Projects** | Node / Python / Java / Go / .NET apps supervised by generated systemd units — port, environment, run-as user, autostart, start-stop-restart, logs |
| **App store** | detect, install and remove 19 packages (nginx, Apache, MySQL, PostgreSQL, Redis, Memcached, MongoDB, PHP, Node, Python, Java, Go, Docker, certbot, Pure-FTPd, Supervisor, fail2ban, git, archive tools) through apt / dnf / yum / zypper / pacman / apk, plus system updates |
| **PHP** | every installed version, php.ini editing by key or by hand (with a backup), extension list, FPM pool config, service control, slow log |
| **Docker** | containers with logs, inspect and live stats; images with pull and prune; networks; volumes; Compose up / down / pull / restart |
| **FTP** | Pure-FTPd virtual users — home directory, quota, password rotation, enable-disable, transfer log |
| **Files** | browse, edit with syntax detection, upload (streamed, up to 2GB), remote download by URL, move, copy, duplicate, chmod, chown, zip/tar compress and extract, archive preview, filename and content search, per-directory disk usage, and a recycle bin with restore |
| **Monitor** | a sampler writing CPU, memory, swap, load, disk, disk I/O, network throughput, process and connection counts to SQLite, with 1h–7d history charts, summaries and retention |
| **Security** | a scored audit of 12 checks, firewall rules over ufw / firewalld / iptables, IP allow/deny for the server or the panel alone, listening-port view, sshd editing with rollback, authorized_keys management, SSH login and brute-force reports, kernel hardening check, panel login throttling, and a web-shell scan |
| **Toolbox** | hostname, timezone, DNS servers and lookup, swap file create/remove, release memory, tunable kernel parameters, open ports, reboot |
| **Cron** | jobs stored in SQLite and rendered into a dedicated `/etc/cron.d/slimpanel` file, run-now, per-job logs |
| **Backups** | site tarballs and database dumps, back up everything in one call, restore a site or a database, download, prune, and copy to remote storage (another directory, S3-compatible, FTP, SFTP, rsync, WebDAV) with a credentials probe |
| **Alerts** | webhook, Slack, DingTalk, WeCom, Telegram and SMTP channels; threshold rules on CPU, memory, swap, load, disk, certificate expiry and service state, with cooldowns and a delivery history |
| **Logs** | per-site access and error tails, a traffic report (requests, unique visitors, bandwidth, status codes, top paths and addresses, referers, crawlers, hourly histogram), grouped error messages, rotation and truncation, disk footprint, panel operation and login logs |
| **Tasks** | long jobs (installs, image pulls, uploads, deployments) run in the background with live output and cancel |
| **One-click** | WordPress with its database and `wp-config.php`, a Laravel skeleton, phpMyAdmin, Adminer, or a styled static placeholder |
| **Auth & API** | session cookie, scrypt hashing, TOTP two-factor, login throttling, panel IP allowlist, audit logs, optional secret entry path, panel HTTPS, and signed or bearer API keys |
| **Terminal** | WebSocket PTY shell |
| **Import** | read an existing aaPanel install and bring over its sites, domains, certificates, rewrite rules, databases and cron jobs |

The web interface is Vue 3 + Vite + Naive UI: 23 pages behind a grouped
sidebar, light and dark themes, and ⌘K / Ctrl-K to jump anywhere.

## Requirements

- Linux with nginx
- Python 3.10+
- Optional, each unlocking its own page: MySQL/MariaDB, PostgreSQL, MongoDB,
  Redis, PHP-FPM, Docker, Pure-FTPd, certbot, ufw or firewalld

Everything optional degrades to a page that says what to install and offers to
install it, rather than an error.

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

Re-running the installer upgrades in place; the schema migrates itself on
start, so an upgrade is `git pull && systemctl restart slimpanel`. To remove the
service and the nginx include while keeping your data:

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
stale database records, and cron jobs whose script is missing. Cron jobs whose
script calls aaPanel internals are imported but left disabled, because they
break once aaPanel is gone.

**Imported sites are parked.** Their vhosts are written as `*.conf.disabled` so
nginx keeps serving aaPanel's copies and no `server_name` conflicts appear. The
cutover is yours to make:

1. `import-aapanel --apply`, then check each site under **Websites**
2. remove aaPanel's include from `nginx.conf`
3. add SlimPanel's include
4. start the sites in SlimPanel, or re-run the import with `--activate`
5. `nginx -t && nginx -s reload`

Roll back by reversing steps 2 and 3 — aaPanel's own vhost files are never
modified.

## Configuration

`slimpanel.json` in the project root, or `SLIMPANEL_<FIELD>` environment
variables, which win over the file. Copy `slimpanel.example.json` to start, or
edit most of it under **Settings** in the UI.

| Key | Default | Notes |
|---|---|---|
| `port` | `8899` | panel listen port |
| `entry_path` | `""` | serve everything under a secret prefix, e.g. `"/x7kq"` |
| `data_dir` | `./data` | database, vhosts, certs, backups, recycle bin |
| `www_root` | `/www/wwwroot` | where new site roots are created |
| `log_root` | `/www/wwwlogs` | where vhost logs are written |
| `file_roots` | `["/www/wwwroot", "/www/wwwlogs"]` | the only paths the file manager may touch |
| `ftp_root` | follows `www_root` | where FTP homes are created |
| `managed_services` | nginx, apache, mysql, redis, docker, … | the only services the panel may control |
| `php_fpm_socket` | `unix:/run/php/php{version}-fpm.sock` | `{version}` comes from the site |
| `php_roots` | `/www/server/php`, `/usr/local/php`, `/etc/php` | where to look for PHP builds |
| `nginx_bin` | `auto` | detected from the running nginx, then `$PATH`; set it explicitly if you run several |
| `firewall_backend` | `auto` | `ufw`, `firewalld` or `iptables` |
| `sshd_config` | `/etc/ssh/sshd_config` | what the Security page edits |
| `cron_target` | `/etc/cron.d/slimpanel` | written additively, never touches existing crontabs |
| `monitor_enabled` | `true` | run the sampling thread |
| `monitor_interval` | `60` | seconds between samples |
| `monitor_retention_days` | `30` | how long history is kept |
| `recycle_bin` | `true` | file deletions go to the bin first |
| `login_max_attempts` | `5` | failed panel logins before an address is locked out |
| `login_block_minutes` | `30` | how long that lockout lasts |
| `panel_ip_allowlist` | `[]` | if non-empty, only these addresses may reach the panel |
| `panel_ssl` | `false` | serve the panel over HTTPS |
| `dry_run` | `false` | log shell commands instead of running them |

SlimPanel writes its vhosts to its own directory and its cron entries to its own
`cron.d` file, so it can be installed next to an existing panel without touching
that panel's configuration.

The panel finds nginx by looking at the running master process first, so on a
host where another panel ships its own build (aaPanel puts 1.24 in
`/www/server/nginx/sbin/nginx` while Ubuntu's 1.18 sits in `/usr/sbin`) it tests
and reloads the one actually serving your sites. The result is cached, because
scanning the process table on every vhost write was the slowest thing the panel
did. The generated vhost follows that binary's version too: HTTP/2 is written as
a `listen` flag below nginx 1.25.1 and as its own `http2 on;` directive from
1.25.1 up.

## Layout

```
app/
  api/           HTTP routes, one module per area (25 routers, 300 endpoints)
  cli.py         serve, import-aapanel, inspect-aapanel, create-user, set-password
  services/      the actual work, one module per concern
  templates/     nginx vhost and upstream Jinja2 templates
  static/dist/   the built web interface, committed so installs need no Node
web/
  src/views/     one Vue file per page (23)
  src/components/ gauges, charts and the command palette
tests/           417 tests, all offline
deploy/          systemd unit and nginx snippet
```

Adding a feature is still three files: a function in `app/services/`, a route in
`app/api/`, a view in `web/src/views/`.

## The API

Every page is a thin client over the REST API, browsable at `/api/docs`. Scripts
authenticate with an API key created under **API keys**, either as a bearer
secret over HTTPS:

```bash
curl -H "X-Api-Key: sp_…" -H "X-Api-Secret: …" https://panel:8899/api/sites
```

or with a signature, which keeps the secret off the wire —
`X-Api-Signature` is `HMAC-SHA256(secret, "key_id:timestamp")` and is accepted
for five minutes. A key can be fenced to a list of addresses.

## Web interface

Vue 3 + Vite + [Naive UI](https://www.naiveui.com/), hash-routed, served by the
panel itself from `app/static/dist`. ~1.6 MB of built assets, code-split per
page.

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

417 tests against a temporary data directory with `dry_run` enabled, so they
never call nginx, systemd, certbot, Docker or MySQL. They cover the generated
nginx config for every site shape, the validation on every input the panel
accepts, path-traversal refusals, archive-extraction escapes, the recycle bin,
login throttling, alert evaluation and the aaPanel importer.

The generated vhosts are separately checked against a real `nginx -t` for all
nine site shapes, including a pool shared by two sites.

## Security notes

The panel runs as root because it edits nginx config and controls services.

- Every file-manager path is resolved with `realpath` and must land inside
  `file_roots`; symlink escapes and `..` are rejected.
- Archive extraction refuses entries that escape the target directory or that
  are links.
- Site names, database identifiers, nginx locations, proxy targets, upstream
  node addresses, Docker references and port mappings are all validated against
  an allowlist before they reach a shell or a config file.
- Cron commands may not contain newlines or `%`.
- Only services listed in `managed_services` can be started or stopped; sshd is
  deliberately not among them, so stopping SSH takes a deliberate act on the
  Security page.
- Only a published set of php.ini, sshd and sysctl keys can be written, each
  with a backup and a config test that rolls back on failure.
- Failed panel logins are counted per address and locked out; a successful login
  clears the counter.
- API secrets are stored salted-hashed and shown once.
- Put the panel behind a firewall rule, set `entry_path`, fill
  `panel_ip_allowlist`, turn on panel HTTPS, and enable TOTP. The Security page
  scores exactly this and tells you what is missing.

## License

MIT
