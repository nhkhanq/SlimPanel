#!/usr/bin/env bash
set -euo pipefail

PANEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PANEL_DIR"

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

[ -f slimpanel.json ] || cp slimpanel.example.json slimpanel.json

echo
echo "SlimPanel installed in $PANEL_DIR"
echo
echo "1. Review $PANEL_DIR/slimpanel.json"
echo "2. Add this line inside the http { } block of your nginx.conf:"
echo
echo "     include $PANEL_DIR/data/vhost/nginx/*.conf;"
echo
echo "   then: nginx -t && nginx -s reload"
echo "3. Start the panel:"
echo
echo "     .venv/bin/python runserver.py"
echo
echo "   or install the service:"
echo "     cp deploy/slimpanel.service /etc/systemd/system/"
echo "     systemctl daemon-reload && systemctl enable --now slimpanel"
echo
echo "The generated admin password is written to data/initial_credentials.txt"
