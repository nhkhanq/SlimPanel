"""Firewall rules, IP rules, SSH config editing, the audit and the malware scan."""
from __future__ import annotations

import pytest
from sqlmodel import Session

from app.config import settings
from app.db import engine
from app.services import firewall, safety, sshd


@pytest.mark.parametrize("port", ["notaport", "0", "70000", "80;rm -rf /", "", "80:90:100"])
def test_port_rules_are_validated(client, port):
    response = client.post("/api/security/firewall/rules", json={"port": port})
    assert response.status_code == 400


@pytest.mark.parametrize("port", ["80", "8000:8100", "65535"])
def test_valid_ports_are_accepted(client, port):
    response = client.post("/api/security/firewall/rules", json={"port": port})
    assert response.status_code == 200, response.text
    assert response.json()["port"] == port.replace("-", ":")


def test_port_range_with_a_dash_is_normalised(client):
    created = client.post("/api/security/firewall/rules", json={"port": "8000-8100"})
    assert created.json()["port"] == "8000:8100"


@pytest.mark.parametrize("protocol", ["sctp", "icmp", ""])
def test_protocol_is_restricted(client, protocol):
    response = client.post(
        "/api/security/firewall/rules", json={"port": "80", "protocol": protocol}
    )
    assert response.status_code == 400


def test_action_is_restricted(client):
    response = client.post("/api/security/firewall/rules", json={"port": "80", "action": "reject"})
    assert response.status_code == 400


@pytest.mark.parametrize("source", ["nonsense", "300.1.1.1", "10.0.0.0/99"])
def test_rule_source_must_be_an_address(client, source):
    response = client.post("/api/security/firewall/rules", json={"port": "80", "source": source})
    assert response.status_code == 400


def test_identical_rules_are_refused(client):
    payload = {"port": "4443", "protocol": "tcp", "source": "10.0.0.0/8"}
    assert client.post("/api/security/firewall/rules", json=payload).status_code == 200
    assert client.post("/api/security/firewall/rules", json=payload).status_code == 400


def test_rule_can_be_toggled_and_removed(client):
    rule = client.post("/api/security/firewall/rules", json={"port": "5555"}).json()

    off = client.post(f"/api/security/firewall/rules/{rule['id']}/enabled", params={"enabled": False})
    assert off.json()["enabled"] is False

    assert client.delete(f"/api/security/firewall/rules/{rule['id']}").status_code == 200
    assert client.delete(f"/api/security/firewall/rules/{rule['id']}").status_code == 404


def test_rules_can_be_reapplied(client):
    client.post("/api/security/firewall/rules", json={"port": "6001"})
    client.post("/api/security/firewall/rules", json={"port": "6002"})
    result = client.post("/api/security/firewall/sync").json()
    assert result["applied"] == 2


@pytest.mark.parametrize("address", ["nope", "1.2.3.4.5", ""])
def test_ip_rules_are_validated(client, address):
    assert client.post("/api/security/ip-rules", json={"address": address}).status_code == 400


def test_ip_rule_scope_is_restricted(client):
    response = client.post(
        "/api/security/ip-rules", json={"address": "1.2.3.4", "scope": "galaxy"}
    )
    assert response.status_code == 400


def test_the_same_address_may_have_one_rule_per_scope(client):
    first = {"address": "203.0.113.9", "scope": "server"}
    second = {"address": "203.0.113.9", "scope": "panel"}
    assert client.post("/api/security/ip-rules", json=first).status_code == 200
    assert client.post("/api/security/ip-rules", json=second).status_code == 200
    assert client.post("/api/security/ip-rules", json=first).status_code == 400


def test_panel_scope_rules_are_filtered(client):
    client.post("/api/security/ip-rules", json={"address": "198.51.100.1", "scope": "server"})
    client.post("/api/security/ip-rules", json={"address": "198.51.100.2", "scope": "panel"})

    panel = client.get("/api/security/ip-rules", params={"scope": "panel"}).json()
    assert [row["address"] for row in panel] == ["198.51.100.2"]


def test_panel_deny_blocks_an_address(client):
    client.post("/api/security/ip-rules", json={"address": "198.51.100.5", "scope": "panel", "action": "drop"})
    with Session(engine) as session:
        assert safety.ip_allowed(session, "198.51.100.5") is False
        assert safety.ip_allowed(session, "198.51.100.6") is True


def test_a_panel_accept_rule_turns_the_panel_into_allowlist_only(client):
    client.post("/api/security/ip-rules", json={"address": "10.1.2.3", "scope": "panel", "action": "accept"})
    with Session(engine) as session:
        assert safety.ip_allowed(session, "10.1.2.3") is True
        assert safety.ip_allowed(session, "10.1.2.4") is False


def test_server_scope_rules_do_not_gate_the_panel(client):
    client.post("/api/security/ip-rules", json={"address": "10.9.9.9", "scope": "server", "action": "accept"})
    with Session(engine) as session:
        # A server allow rule is a firewall concern, not a panel login concern.
        assert safety.ip_allowed(session, "10.0.0.1") is True


def test_firewall_status_and_ports_are_reported(client):
    status = client.get("/api/security/firewall").json()
    assert status["backend"] in {"ufw", "firewalld", "iptables", "none"}
    assert isinstance(status["active"], bool)
    assert isinstance(client.get("/api/security/firewall/ports").json(), list)


def test_ssh_options_are_parsed(client):
    body = client.get("/api/security/ssh").json()
    assert "Port" in body["values"]
    assert "PermitRootLogin" in body["editable"]
    assert "yes" in body["editable"]["PasswordAuthentication"]


def test_ssh_rejects_an_option_it_does_not_manage(client):
    response = client.post("/api/security/ssh", json={"values": {"Subsystem": "sftp /bin/sh"}})
    assert response.status_code == 400


def test_ssh_rejects_a_value_outside_the_allowed_set(client):
    response = client.post("/api/security/ssh", json={"values": {"PermitRootLogin": "maybe"}})
    assert response.status_code == 400


def test_ssh_numeric_options_must_be_numbers(client):
    response = client.post("/api/security/ssh", json={"values": {"MaxAuthTries": "lots"}})
    assert response.status_code == 400


def test_ssh_port_range_is_checked(client):
    assert client.post("/api/security/ssh", json={"values": {"Port": "70000"}}).status_code == 400


def test_sshd_patching_supersedes_an_earlier_line(tmp_path, monkeypatch):
    config = tmp_path / "sshd_config"
    config.write_text("Port 22\nPasswordAuthentication yes\nPasswordAuthentication yes\n")
    monkeypatch.setattr(settings, "sshd_config", str(config))
    monkeypatch.setattr(sshd, "test_config", lambda: type("R", (), {"ok": True, "output": ""})())

    sshd.set_values({"PasswordAuthentication": "no"})
    body = config.read_text()

    assert body.count("\nPasswordAuthentication no") == 1
    # sshd honours the first occurrence, so the duplicate has to be commented out.
    assert "# PasswordAuthentication yes" in body
    assert config.with_suffix(".slimpanel.bak").is_file()


def test_sshd_rolls_back_when_sshd_rejects_the_result(tmp_path, monkeypatch):
    config = tmp_path / "sshd_config"
    original = "Port 22\nPasswordAuthentication yes\n"
    config.write_text(original)
    monkeypatch.setattr(settings, "sshd_config", str(config))
    monkeypatch.setattr(
        sshd, "test_config", lambda: type("R", (), {"ok": False, "output": "bad config"})()
    )

    with pytest.raises(Exception):
        sshd.set_values({"Port": "2222"})
    assert config.read_text() == original


def test_public_key_shape_is_checked(client):
    assert client.post("/api/security/ssh/keys", json={"public_key": "hello"}).status_code == 400
    assert client.post(
        "/api/security/ssh/keys", json={"public_key": "ssh-rsa AAA\nssh-rsa BBB"}
    ).status_code == 400


def test_audit_reports_a_score_and_checks(client):
    report = client.get("/api/security/audit").json()
    assert 0 <= report["score"] <= 100
    assert report["total"] == len(report["checks"])
    assert report["passed"] == sum(1 for check in report["checks"] if check["ok"])
    for check in report["checks"]:
        assert check["severity"] in {"high", "medium", "low"}
        assert check["name"]


def test_audit_flags_a_world_writable_site_root(client, www_root):
    root = www_root / "loose"
    root.mkdir(exist_ok=True)
    root.chmod(0o777)
    client.post("/api/sites", json={"name": "loose.test", "site_type": "static", "root": str(root)})

    report = client.get("/api/security/audit").json()
    check = next(c for c in report["checks"] if c["name"] == "Site directory permissions")
    assert check["ok"] is False
    assert "loose.test" in check["detail"]

    root.chmod(0o755)


def test_kernel_hardening_is_reported(client):
    rows = client.get("/api/security/kernel").json()
    assert rows
    assert {"key", "current", "expected", "ok"} <= set(rows[0])


def test_malware_scan_flags_an_obvious_shell(client, www_root):
    root = www_root / "scanme"
    root.mkdir(exist_ok=True)
    (root / "clean.php").write_text("<?php echo 'hello';")
    (root / "shell.php").write_text("<?php eval(base64_decode($_POST['x']));")
    (root / "notphp.txt").write_text("eval(base64_decode('x'))")

    site = client.post(
        "/api/sites", json={"name": "scanme.test", "site_type": "php", "root": str(root)}
    ).json()

    report = client.get(f"/api/security/scan/{site['id']}").json()
    flagged = {entry["path"].rsplit("/", 1)[-1] for entry in report["findings"]}
    assert flagged == {"shell.php"}  # only PHP files, only the suspicious one


def test_malware_scan_needs_a_real_site(client):
    assert client.get("/api/security/scan/9999").status_code == 404


def test_login_attempts_are_recorded_and_clearable(anon, client):
    for _ in range(3):
        anon.post("/api/auth/login", json={"username": "admin", "password": "wrong"})

    rows = client.get("/api/security/login-attempts").json()
    assert rows
    assert rows[0]["attempts"] >= 3

    assert client.delete(f"/api/security/login-attempts/{rows[0]['ip']}").status_code == 200
    assert client.get("/api/security/login-attempts").json() == []


def test_brute_force_lockout_kicks_in(anon):
    for _ in range(settings.login_max_attempts):
        anon.post("/api/auth/login", json={"username": "admin", "password": "wrong"})

    # The correct password is refused too, once the window is used up.
    blocked = anon.post(
        "/api/auth/login", json={"username": "admin", "password": "test-password-123"}
    )
    assert blocked.status_code == 429


def test_ping_toggle_reports_state(client):
    body = client.get("/api/security/ping").json()
    assert isinstance(body["enabled"], bool)


def test_security_endpoints_need_authentication(anon):
    for path in (
        "/api/security/firewall",
        "/api/security/audit",
        "/api/security/ssh",
        "/api/security/ip-rules",
    ):
        assert anon.get(path).status_code == 401, path
