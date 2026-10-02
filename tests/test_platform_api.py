"""PHP, the app store, Docker guards, FTP, the toolbox, tasks and API keys."""
from __future__ import annotations

import time

import pytest
from sqlmodel import Session

from app.config import settings
from app.db import engine
from app.services import apikeys, php, tasks, toolbox


# --------------------------------------------------------------------- PHP


def test_php_versions_are_discovered(client):
    rows = client.get("/api/php").json()
    for row in rows:
        assert row["version"].count(".") == 1
        assert row["service"].startswith("php")
        assert isinstance(row["installed"], bool)


def test_an_unknown_php_version_is_a_404(client):
    assert client.get("/api/php/4.2").status_code == 404
    assert client.get("/api/php/4.2/ini").status_code == 404


def test_php_ini_patching_keeps_comments_and_order(tmp_path, monkeypatch):
    ini = tmp_path / "php.ini"
    ini.write_text(
        "; a comment\n"
        "memory_limit = 128M\n"
        "; memory_limit = 999M\n"
        "upload_max_filesize = 2M\n"
    )
    monkeypatch.setattr(
        php, "get", lambda version: {"version": version, "ini": str(ini), "path": "", "binary": ""}
    )

    php.set_values("8.1", {"memory_limit": "512M", "post_max_size": "64M"})
    body = ini.read_text()

    assert "; a comment" in body
    assert "memory_limit = 512M" in body
    assert "; memory_limit = 999M" in body  # commented-out lines stay commented
    assert "upload_max_filesize = 2M" in body
    assert "post_max_size = 64M" in body  # appended because it was absent
    assert ini.with_suffix(".ini.slimpanel.bak").is_file()


def test_php_ini_only_accepts_known_keys(tmp_path, monkeypatch):
    ini = tmp_path / "php.ini"
    ini.write_text("memory_limit = 128M\n")
    monkeypatch.setattr(
        php, "get", lambda version: {"version": version, "ini": str(ini), "path": "", "binary": ""}
    )
    with pytest.raises(Exception):
        php.set_values("8.1", {"auto_prepend_file": "/tmp/evil.php"})


def test_php_service_actions_are_restricted(client):
    rows = client.get("/api/php").json()
    if not rows:
        pytest.skip("no PHP on this host")
    version = rows[0]["version"]
    assert client.post(f"/api/php/{version}/service/explode").status_code == 400


# --------------------------------------------------------------- app store


def test_catalogue_reports_installed_state(client):
    body = client.get("/api/apps").json()
    slugs = {app["slug"] for app in body["apps"]}
    assert {"nginx", "mysql", "redis", "docker", "php", "nodejs"} <= slugs
    for app in body["apps"]:
        assert app["category"] in {"web", "database", "runtime", "container", "security", "tool"}
        assert isinstance(app["installed"], bool)


def test_installing_an_unknown_app_is_refused(client):
    assert client.post("/api/apps/not-a-thing/install").status_code == 400


def test_config_files_are_listed_for_known_services(client):
    rows = client.get("/api/apps/nginx/config-files").json()
    assert any(row["path"].endswith("nginx.conf") for row in rows)


def test_install_returns_a_task(client):
    task = client.post("/api/apps/git/install")
    assert task.status_code == 200, task.text
    body = task.json()
    assert body["kind"] == "shell"
    assert "git" in body["detail"]


# ------------------------------------------------------------------ docker


def test_docker_endpoints_explain_themselves_when_it_is_absent(client, monkeypatch):
    from app.services import docker

    monkeypatch.setattr(docker, "available", lambda: False)
    info = client.get("/api/docker/info").json()
    assert info["available"] is False
    assert client.get("/api/docker/containers").status_code == 400


@pytest.mark.parametrize(
    "mapping", ["notaport", "80", "80:90:100", "abc:80", "80:70000", "1.2.3:80:90"]
)
def test_docker_port_mappings_are_validated(client, mapping):
    response = client.post("/api/docker/containers", json={"image": "nginx", "ports": [mapping]})
    assert response.status_code == 400


def test_docker_names_are_validated(client):
    response = client.post("/api/docker/containers", json={"image": "nginx", "name": "bad name!"})
    assert response.status_code == 400


def test_docker_restart_policy_is_validated(client):
    response = client.post("/api/docker/containers", json={"image": "nginx", "restart": "whenever"})
    assert response.status_code == 400


def test_docker_prune_target_is_restricted(client):
    assert client.post("/api/docker/prune/everything").status_code == 400


def test_compose_file_must_be_yaml(client, www_root):
    response = client.post(
        "/api/docker/compose/write",
        json={"path": str(www_root / "compose.txt"), "content": "services: {}"},
    )
    assert response.status_code == 400


def test_compose_action_is_restricted(client, www_root):
    response = client.post(
        "/api/docker/compose", json={"compose_file": str(www_root / "a.yml"), "action": "nuke"}
    )
    assert response.status_code == 400


# --------------------------------------------------------------------- FTP


def test_ftp_status_names_a_backend(client):
    body = client.get("/api/ftp/status").json()
    assert body["backend"] in {"pure-ftpd", "vsftpd", "none"}


@pytest.mark.parametrize("username", ["has space", "sym!bol", "a" * 40, ""])
def test_ftp_usernames_are_validated(client, username):
    response = client.post("/api/ftp", json={"username": username, "password": "longenough1"})
    assert response.status_code == 400


def test_ftp_password_has_a_minimum(client):
    response = client.post("/api/ftp", json={"username": "shorty", "password": "abc"})
    assert response.status_code == 400


def test_ftp_user_lifecycle(client):
    created = client.post("/api/ftp", json={"username": "deploy", "quota_mb": 500})
    assert created.status_code == 200, created.text
    user = created.json()
    assert len(user["password"]) >= 16  # generated
    assert user["home"].endswith("/deploy")

    assert client.post("/api/ftp", json={"username": "deploy"}).status_code == 409

    rotated = client.post(f"/api/ftp/{user['id']}/password", json={"password": ""}).json()
    assert rotated["password"] != user["password"]

    quota = client.post(f"/api/ftp/{user['id']}/quota", json={"quota_mb": 1000}).json()
    assert quota["quota_mb"] == 1000

    off = client.post(f"/api/ftp/{user['id']}/enabled", params={"enabled": False}).json()
    assert off["enabled"] is False

    assert client.delete(f"/api/ftp/{user['id']}").status_code == 200
    assert client.get("/api/ftp").json() == []


def test_ftp_negative_quota_is_refused(client):
    user = client.post("/api/ftp", json={"username": "quotatest"}).json()
    assert client.post(f"/api/ftp/{user['id']}/quota", json={"quota_mb": -5}).status_code == 400


def test_ftp_home_must_stay_in_the_managed_roots(client):
    response = client.post("/api/ftp", json={"username": "escapee", "home": "/etc/cron.d"})
    assert response.status_code == 403


# ----------------------------------------------------------------- toolbox


def test_toolbox_reports_the_basics(client):
    body = client.get("/api/toolbox").json()
    assert body["hostname"]
    assert body["kernel"]
    assert isinstance(body["dns"], list)


@pytest.mark.parametrize("name", ["not a zone", "../etc/passwd", ""])
def test_timezone_is_validated(client, name):
    assert client.post("/api/toolbox/timezone", json={"name": name}).status_code == 400


@pytest.mark.parametrize("name", ["has space", "bad/slash", "-leading", ""])
def test_hostname_is_validated(client, name):
    assert client.post("/api/toolbox/hostname", json={"name": name}).status_code == 400


def test_dns_servers_must_be_addresses(client):
    assert client.post("/api/toolbox/dns", json={"servers": ["notanip"]}).status_code == 400
    assert client.post("/api/toolbox/dns", json={"servers": []}).status_code == 400


def test_resolve_refuses_shell_metacharacters(client):
    assert client.get("/api/toolbox/resolve", params={"host": "a.test; rm -rf /"}).status_code == 400


@pytest.mark.parametrize("size", [1, 63, 100000])
def test_swap_size_bounds(client, size):
    assert client.post("/api/toolbox/swap", json={"size_mb": size}).status_code == 400


def test_sysctl_only_accepts_the_published_keys(client):
    assert client.post(
        "/api/toolbox/sysctl", json={"values": {"kernel.core_pattern": "|/bin/sh"}}
    ).status_code == 400


def test_sysctl_values_must_be_numeric(client):
    assert client.post(
        "/api/toolbox/sysctl", json={"values": {"vm.swappiness": "a lot"}}
    ).status_code == 400


def test_sysctl_accepts_a_space_separated_range():
    # net.ipv4.ip_local_port_range is two numbers, so digits alone is too strict.
    assert "net.ipv4.ip_local_port_range" in toolbox.TUNABLE_SYSCTL


def test_ftp_root_follows_the_web_root():
    # Leaving ftp_root pinned to /www/wwwroot breaks FTP once www_root moves.
    assert settings.ftp_root == settings.www_root


def test_reboot_needs_the_confirmation_word(client):
    body = client.post("/api/toolbox/reboot").json()
    assert body["ok"] is False
    assert "confirm=reboot" in body["message"]


# ------------------------------------------------------------------- tasks


def test_a_shell_task_runs_and_records_its_output(client):
    with Session(engine) as session:
        # dry_run short-circuits the subprocess, so drive the real path directly.
        task = tasks.create(session, "unit test", kind="shell", detail="echo hi")
        tasks._finish(task.id, "done", "exit=0")

    rows = client.get("/api/tasks").json()
    assert rows[0]["status"] == "done"
    assert client.get(f"/api/tasks/{rows[0]['id']}/output").status_code == 200


def test_cancelling_a_finished_task_says_so(client):
    with Session(engine) as session:
        task = tasks.create(session, "already done")
        tasks._finish(task.id, "done")

    body = client.post(f"/api/tasks/{task.id}/cancel").json()
    assert body["ok"] is False
    assert "already finished" in body["message"]


def test_a_pending_task_can_be_cancelled(client):
    with Session(engine) as session:
        task = tasks.create(session, "waiting")

    assert client.post(f"/api/tasks/{task.id}/cancel").json()["ok"] is True
    assert client.get(f"/api/tasks/{task.id}").json()["status"] == "cancelled"


def test_task_pruning_keeps_the_newest(client):
    with Session(engine) as session:
        for index in range(12):
            tasks.create(session, f"task {index}")

    body = client.post("/api/tasks/prune", params={"keep": 5}).json()
    assert "Removed 7" in body["message"]
    assert len(client.get("/api/tasks").json()) == 5


def test_tasks_can_be_filtered_by_status(client):
    with Session(engine) as session:
        done = tasks.create(session, "done one")
        tasks._finish(done.id, "done")
        tasks.create(session, "pending one")

    rows = client.get("/api/tasks", params={"status": "done"}).json()
    assert [row["name"] for row in rows] == ["done one"]


# ---------------------------------------------------------------- API keys


def test_api_key_is_shown_once_then_only_fingerprinted(client):
    created = client.post("/api/api-keys", json={"name": "deploy"}).json()
    assert created["secret"]

    listed = client.get("/api/api-keys").json()
    assert "secret" not in listed[0]
    assert len(listed[0]["fingerprint"]) == 16


def test_api_key_allow_list_is_validated(client):
    assert client.post("/api/api-keys", json={"name": "x", "allow_ips": "nonsense"}).status_code == 400


def test_api_key_authenticates_by_secret_and_by_signature(client):
    created = client.post("/api/api-keys", json={"name": "both"}).json()

    with Session(engine) as session:
        by_secret = apikeys.verify(session, created["key_id"], secret=created["secret"])
        assert by_secret.name == "both"

        headers = apikeys.sign(created["key_id"], created["secret"])
        by_signature = apikeys.verify(
            session,
            headers["X-Api-Key"],
            timestamp=headers["X-Api-Timestamp"],
            presented_signature=headers["X-Api-Signature"],
        )
        assert by_signature.name == "both"


def test_api_key_rejects_a_stale_signature(client):
    created = client.post("/api/api-keys", json={"name": "stale"}).json()
    old = int(time.time()) - apikeys.SIGNATURE_WINDOW - 60
    headers = apikeys.sign(created["key_id"], created["secret"], timestamp=old)

    with Session(engine) as session:
        with pytest.raises(Exception, match="signing window"):
            apikeys.verify(
                session, headers["X-Api-Key"], timestamp=headers["X-Api-Timestamp"],
                presented_signature=headers["X-Api-Signature"],
            )


def test_api_key_honours_its_allow_list(client):
    created = client.post("/api/api-keys", json={"name": "fenced", "allow_ips": "10.0.0.0/8"}).json()
    with Session(engine) as session:
        assert apikeys.verify(session, created["key_id"], ip="10.1.2.3", secret=created["secret"])
        with pytest.raises(Exception, match="not allowed"):
            apikeys.verify(session, created["key_id"], ip="203.0.113.1", secret=created["secret"])


def test_a_disabled_api_key_is_refused(client):
    created = client.post("/api/api-keys", json={"name": "off"}).json()
    client.post(f"/api/api-keys/{created['id']}/enabled", params={"enabled": False})

    with Session(engine) as session:
        with pytest.raises(Exception, match="disabled"):
            apikeys.verify(session, created["key_id"], secret=created["secret"])


def test_api_key_needs_a_credential(client):
    created = client.post("/api/api-keys", json={"name": "bare"}).json()
    with Session(engine) as session:
        with pytest.raises(Exception, match="X-Api-Secret"):
            apikeys.verify(session, created["key_id"])


def test_a_task_removed_mid_run_does_not_raise(client):
    """The UI can delete a running task; the worker must not blow up writing back."""
    with Session(engine) as session:
        task = tasks.create(session, "vanishing")
        tasks.delete(session, task.id)

    tasks._start(task.id)
    tasks._finish(task.id, "done", "exit=0")
    assert client.get(f"/api/tasks/{task.id}").status_code == 404
