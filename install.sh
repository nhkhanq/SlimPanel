#!/usr/bin/env bash
# SlimPanel installer.
#   curl -fsSL https://raw.githubusercontent.com/nhkhanq/SlimPanel/main/install.sh | sudo bash
set -euo pipefail

REPO="${SLIMPANEL_REPO:-https://github.com/nhkhanq/SlimPanel.git}"
BRANCH="${SLIMPANEL_BRANCH:-main}"
DIR="${SLIMPANEL_DIR:-/www/SlimPanel}"
PORT="${SLIMPANEL_PORT:-8899}"
SERVICE="${SLIMPANEL_SERVICE:-slimpanel}"
SKIP_SERVICE="${SLIMPANEL_SKIP_SERVICE:-0}"
SKIP_NGINX="${SLIMPANEL_SKIP_NGINX:-0}"
SKIP_DEPS="${SLIMPANEL_SKIP_DEPS:-0}"

say()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

require_root() {
  [ "$(id -u)" = "0" ] || die "Run as root: curl -fsSL <url> | sudo bash"
}

install_system_deps() {
  [ "$SKIP_DEPS" = "1" ] && return 0
  local missing=()
  command -v git >/dev/null || missing+=(git)
  python3 -c 'import venv, ensurepip' 2>/dev/null || missing+=(python3-venv python3-pip)
  [ ${#missing[@]} -eq 0 ] && return 0

  say "Installing: ${missing[*]}"
  if command -v apt-get >/dev/null; then
    DEBIAN_FRONTEND=noninteractive apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing[@]}"
  elif command -v dnf >/dev/null; then
    dnf install -y git python3-pip
  elif command -v yum >/dev/null; then
    yum install -y git python3-pip
  else
    die "Unsupported package manager. Install git and python3-venv manually, then re-run."
  fi
}

check_python() {
  command -v python3 >/dev/null || die "python3 is required"
  python3 - <<'PY' || die "Python 3.10+ is required"
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
}

fetch_source() {
  if [ -d "$DIR/.git" ]; then
    say "Updating $DIR"
    git -C "$DIR" fetch --depth 1 origin "$BRANCH"
    git -C "$DIR" reset --hard "origin/$BRANCH"
  else
    say "Cloning into $DIR"
    mkdir -p "$(dirname "$DIR")"
    git clone --depth 1 --branch "$BRANCH" "$REPO" "$DIR"
  fi
}

build_venv() {
  say "Building virtualenv"
  python3 -m venv "$DIR/.venv"
  "$DIR/.venv/bin/python" -m pip install --quiet --upgrade pip
  "$DIR/.venv/bin/python" -m pip install --quiet -r "$DIR/requirements.txt"
}

write_config() {
  local config="$DIR/slimpanel.json"
  if [ ! -f "$config" ]; then
    say "Writing $config"
    "$DIR/.venv/bin/python" - "$config" "$PORT" <<'PY'
import json, sys
from pathlib import Path

target, port = Path(sys.argv[1]), int(sys.argv[2])
template = json.loads((target.parent / "slimpanel.example.json").read_text())
template["port"] = port
target.write_text(json.dumps(template, indent=2) + "\n")
PY
    chmod 600 "$config"
  fi
}

configure_nginx() {
  [ "$SKIP_NGINX" = "1" ] && return 0
  command -v nginx >/dev/null || { warn "nginx not found, skipping include"; return 0; }

  local snippet="include $DIR/data/vhost/nginx/*.conf;"
  if nginx -T 2>/dev/null | grep -qF "$DIR/data/vhost/nginx"; then
    say "nginx include already present"
    return 0
  fi

  if [ -d /etc/nginx/conf.d ] && nginx -T 2>/dev/null | grep -q "/etc/nginx/conf.d"; then
    say "Adding /etc/nginx/conf.d/slimpanel.conf"
    echo "$snippet" > /etc/nginx/conf.d/slimpanel.conf
    if nginx -t >/dev/null 2>&1; then
      nginx -s reload || true
    else
      rm -f /etc/nginx/conf.d/slimpanel.conf
      warn "nginx -t failed, include removed. Add it manually."
    fi
    return 0
  fi

  warn "Could not find a drop-in directory. Add this inside the http { } block of your nginx.conf:"
  printf '\n    %s\n\n' "$snippet"
}

install_service() {
  [ "$SKIP_SERVICE" = "1" ] && return 0
  command -v systemctl >/dev/null || { warn "systemd not found, start manually"; return 0; }

  say "Installing systemd unit"
  sed "s|/www/SlimPanel|$DIR|g" "$DIR/deploy/slimpanel.service" > "/etc/systemd/system/$SERVICE.service"
  systemctl daemon-reload
  systemctl enable --quiet "$SERVICE"
  systemctl restart "$SERVICE"
}

wait_for_health() {
  [ "$SKIP_SERVICE" = "1" ] && return 0
  say "Waiting for the panel"
  for _ in $(seq 1 40); do
    if "$DIR/.venv/bin/python" - "$PORT" <<'PY' 2>/dev/null
import sys, urllib.request
urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/healthz", timeout=1)
PY
    then return 0; fi
    sleep 0.5
  done
  warn "Panel did not answer yet. Check: journalctl -u $SERVICE -n 50"
}

report() {
  local ip
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  echo
  say "SlimPanel is installed"
  echo "   URL:      http://${ip:-<server-ip>}:$PORT"
  if [ -f "$DIR/data/initial_credentials.txt" ]; then
    echo "   Login:"
    sed 's/^/     /' "$DIR/data/initial_credentials.txt"
  fi
  echo
  echo "   Service:  systemctl status $SERVICE"
  echo "   Logs:     journalctl -u $SERVICE -f"
  echo "   Import:   $DIR/.venv/bin/python -m app.cli import-aapanel"
  echo
}

main() {
  require_root
  check_python
  install_system_deps
  fetch_source
  build_venv
  write_config
  configure_nginx
  install_service
  wait_for_health
  report
}

main "$@"
