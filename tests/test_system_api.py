def test_overview_shape(client):
    data = client.get("/api/system/overview").json()
    assert {"cpu", "memory", "disks", "load", "network", "uptime_seconds"} <= data.keys()
    assert data["cpu"]["cores"] >= 1
    assert data["memory"]["total"] > 0


def test_processes_are_limited_and_sorted(client):
    rows = client.get("/api/system/processes", params={"limit": 5}).json()
    assert len(rows) <= 5
    assert rows == sorted(rows, key=lambda row: row["cpu_percent"], reverse=True)


def test_kill_refuses_init(client):
    assert client.post("/api/system/processes/1/kill").status_code == 400


def test_services_listed(client):
    names = [row["name"] for row in client.get("/api/system/services").json()]
    assert "nginx" in names


def test_unmanaged_service_is_rejected(client):
    response = client.post("/api/system/services", json={"name": "sshd", "action": "stop"})
    assert response.status_code == 400


def test_unknown_action_is_rejected(client):
    response = client.post("/api/system/services", json={"name": "nginx", "action": "destroy"})
    assert response.status_code == 400


def test_settings_hide_secrets(client):
    data = client.get("/api/system/settings").json()
    assert "secret_key" not in data
    assert "mysql_password" not in data
    assert data["nginx_include_snippet"].startswith("include ")


def test_nginx_test_endpoint(client):
    assert client.get("/api/system/nginx/test").json()["ok"] is True


def test_healthz_is_public(anon):
    assert anon.get("/healthz").json() == {"ok": True}


def test_spa_is_served_at_root(anon):
    response = anon.get("/")
    assert response.status_code == 200
    assert "<div id=\"app\">" in response.text or "not built" in response.text


def test_api_routes_win_over_the_spa_mount(anon):
    assert anon.get("/api/sites").status_code == 401
    assert anon.get("/api/auth/me").status_code == 401
