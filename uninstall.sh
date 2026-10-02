#!/usr/bin/env bash
set -euo pipefail

DIR="${SLIMPANEL_DIR:-/www/SlimPanel}"
SERVICE="${SLIMPANEL_SERVICE:-slimpanel}"

[ "$(id -u)" = "0" ] || { echo "Run as root" >&2; exit 1; }

if command -v systemctl >/dev/null; then
  systemctl disable --now "$SERVICE" 2>/dev/null || true
  rm -f "/etc/systemd/system/$SERVICE.service"
  systemctl daemon-reload
fi

rm -f /etc/nginx/conf.d/slimpanel.conf /etc/cron.d/slimpanel
command -v nginx >/dev/null && nginx -t >/dev/null 2>&1 && nginx -s reload || true

echo "Service and nginx include removed."
echo "Panel files and data are still at $DIR - delete them yourself if you want them gone:"
echo "  rm -rf $DIR"
