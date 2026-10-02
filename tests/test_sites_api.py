from app.services import nginx


def create_site(client, name="demo.test", **extra):
    payload = {"name": name, "site_type": "static", "domains": [name]}
    payload.update(extra)
    return client.post("/api/sites", json=payload)


def test_create_site_writes_vhost_and_root(client, www_root):
    response = create_site(client)
    assert response.status_code == 200, response.text

    site = response.json()
    assert site["name"] == "demo.test"
    assert site["domains"] == ["demo.test"]
    assert (www_root / "demo.test" / "index.html").exists()
    assert nginx.vhost_file("demo.test").exists()


def test_duplicate_site_is_rejected(client):
    create_site(client)
    assert create_site(client).status_code == 409


def test_invalid_site_name_is_rejected(client):
    assert create_site(client, name="../etc/passwd").status_code == 403


def test_proxy_site_requires_target(client):
    response = create_site(client, name="api.test", site_type="proxy")
    assert response.status_code == 400

    ok = create_site(
        client, name="api.test", site_type="proxy", proxy_target="http://127.0.0.1:3000"
    )
    assert ok.status_code == 200
    config = client.get(f"/api/sites/{ok.json()['id']}/config").json()
    assert "proxy_pass http://127.0.0.1:3000;" in config["content"]


def test_update_site_rewrites_config(client):
    site_id = create_site(client).json()["id"]
    response = client.patch(
        f"/api/sites/{site_id}", json={"run_path": "public", "index_files": "index.htm"}
    )
    assert response.status_code == 200
    assert response.json()["run_path"] == "public"

    config = client.get(f"/api/sites/{site_id}/config").json()
    assert "/demo.test/public;" in config["content"]
    assert "index index.htm;" in config["content"]


def test_stop_and_start_site(client):
    site_id = create_site(client).json()["id"]

    client.post(f"/api/sites/{site_id}/stop")
    assert nginx.disabled_vhost_file("demo.test").exists()
    assert client.get(f"/api/sites/{site_id}").json()["enabled"] is False

    client.post(f"/api/sites/{site_id}/start")
    assert nginx.vhost_file("demo.test").exists()
    assert client.get(f"/api/sites/{site_id}").json()["enabled"] is True


def test_domain_add_and_remove(client):
    site_id = create_site(client).json()["id"]
    added = client.post(f"/api/sites/{site_id}/domains", json={"name": "www.demo.test"})
    assert added.status_code == 200

    config = client.get(f"/api/sites/{site_id}/config").json()
    assert "server_name demo.test www.demo.test;" in config["content"]

    removed = client.delete(f"/api/sites/{site_id}/domains/{added.json()['id']}")
    assert removed.status_code == 200

    duplicate = client.post(f"/api/sites/{site_id}/domains", json={"name": "demo.test"})
    assert duplicate.status_code == 409


def test_last_domain_cannot_be_removed(client):
    site_id = create_site(client).json()["id"]
    domains = client.get(f"/api/sites/{site_id}/domains").json()
    assert len(domains) == 1

    only = client.post(f"/api/sites/{site_id}/domains", json={"name": "second.test"})
    client.delete(f"/api/sites/{site_id}/domains/{only.json()['id']}")
    remaining = client.get(f"/api/sites/{site_id}").json()["domains"]
    assert remaining == ["demo.test"]


def test_delete_site_keeps_files_by_default(client, www_root):
    site_id = create_site(client).json()["id"]
    assert client.delete(f"/api/sites/{site_id}").status_code == 200
    assert not nginx.vhost_file("demo.test").exists()
    assert (www_root / "demo.test").exists()


def test_delete_site_with_files(client, www_root):
    site_id = create_site(client, name="gone.test").json()["id"]
    client.delete(f"/api/sites/{site_id}?remove_files=true")
    assert not (www_root / "gone.test").exists()


def test_ssl_lifecycle_in_dry_run(client):
    site_id = create_site(client).json()["id"]
    issued = client.post(
        f"/api/ssl/{site_id}/issue", json={"domains": ["demo.test"], "force_https": True}
    )
    assert issued.status_code == 200, issued.text

    status = client.get(f"/api/ssl/{site_id}").json()
    assert status["ssl_enabled"] is True
    assert status["force_https"] is True

    config = client.get(f"/api/sites/{site_id}/config").json()["content"]
    assert "listen 443 ssl;" in config
    assert "return 301 https://$host$request_uri;" in config

    client.post(f"/api/ssl/{site_id}/disable")
    assert client.get(f"/api/ssl/{site_id}").json()["ssl_enabled"] is False
