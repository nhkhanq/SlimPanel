"""Redirects, extra proxies, directory passwords, pools and the rewrite library."""
from __future__ import annotations

import pytest

from app.services import nginx


@pytest.fixture
def site(client):
    response = client.post(
        "/api/sites",
        json={"name": "extras.test", "site_type": "static", "domains": ["extras.test"]},
    )
    assert response.status_code == 200, response.text
    return response.json()


def rendered(client, site_id: int) -> str:
    return client.get(f"/api/sites/{site_id}/config").json()["rendered"]


def test_site_groups_round_trip(client):
    created = client.post("/api/sites/groups", json={"name": "Production"})
    assert created.status_code == 200
    group = created.json()

    assert client.post("/api/sites/groups", json={"name": "Production"}).status_code == 409

    site = client.post(
        "/api/sites", json={"name": "grouped.test", "site_type": "static", "group_id": group["id"]}
    ).json()
    assert site["group_id"] == group["id"]
    assert site["group_name"] == "Production"

    # Removing a group unbinds its sites rather than deleting them.
    assert client.delete(f"/api/sites/groups/{group['id']}").status_code == 200
    assert client.get(f"/api/sites/{site['id']}").json()["group_id"] is None


def test_unknown_group_is_rejected(client):
    response = client.post(
        "/api/sites", json={"name": "nogroup.test", "site_type": "static", "group_id": 9999}
    )
    assert response.status_code == 404


def test_path_redirect_renders_a_location(client, site):
    created = client.post(
        f"/api/sites/{site['id']}/redirects",
        json={"source": "/old", "target": "https://extras.test/new", "code": 301, "keep_path": False},
    )
    assert created.status_code == 200, created.text

    config = rendered(client, site["id"])
    assert "location /old {" in config
    assert "return 301 https://extras.test/new;" in config


def test_domain_redirect_renders_its_own_server_block(client, site):
    client.post(
        f"/api/sites/{site['id']}/redirects",
        json={"kind": "domain", "source": "legacy.test", "target": "https://extras.test", "code": 302},
    )
    config = rendered(client, site["id"])
    assert "server_name legacy.test;" in config
    assert "return 302 https://extras.test$request_uri;" in config


@pytest.mark.parametrize("code", [200, 404, 418])
def test_redirect_code_must_be_a_redirect(client, site, code):
    response = client.post(
        f"/api/sites/{site['id']}/redirects",
        json={"source": "/x", "target": "https://a.test", "code": code},
    )
    assert response.status_code == 400


@pytest.mark.parametrize("target", ["ftp://host/x", "javascript:alert(1)", "not a url", ""])
def test_redirect_target_must_be_http(client, site, target):
    response = client.post(
        f"/api/sites/{site['id']}/redirects", json={"source": "/x", "target": target}
    )
    assert response.status_code == 400


def test_disabled_redirect_leaves_the_vhost(client, site):
    created = client.post(
        f"/api/sites/{site['id']}/redirects",
        json={"source": "/gone", "target": "https://extras.test/here"},
    ).json()

    client.post(f"/api/sites/redirects/{created['id']}/enabled/false")
    assert "location /gone {" not in rendered(client, site["id"])

    client.post(f"/api/sites/redirects/{created['id']}/enabled/true")
    assert "location /gone {" in rendered(client, site["id"])


def test_proxy_rule_renders_with_cache_and_replacements(client, site):
    created = client.post(
        f"/api/sites/{site['id']}/proxies",
        json={
            "location": "/api",
            "target": "http://127.0.0.1:9000",
            "cache_enabled": True,
            "cache_time": 120,
            "replace_rules": "http://internal|https://extras.test\nbad|good",
        },
    )
    assert created.status_code == 200, created.text

    config = rendered(client, site["id"])
    assert "location /api {" in config
    assert "proxy_pass http://127.0.0.1:9000;" in config
    assert "proxy_cache_valid 200 304 301 302 120s;" in config
    assert 'sub_filter "http://internal" "https://extras.test";' in config
    assert 'sub_filter "bad" "good";' in config
    # text/html is already in nginx's default sub_filter_types; repeating it warns.
    assert "sub_filter_types text/css" in config
    assert "sub_filter_types text/html" not in config


def test_two_proxies_cannot_share_a_location(client, site):
    first = {"location": "/api", "target": "http://127.0.0.1:9000"}
    assert client.post(f"/api/sites/{site['id']}/proxies", json=first).status_code == 200
    assert client.post(f"/api/sites/{site['id']}/proxies", json=first).status_code == 409


def test_a_proxy_on_root_replaces_the_default_location(client, site):
    client.post(
        f"/api/sites/{site['id']}/proxies",
        json={"location": "/", "target": "http://127.0.0.1:9000"},
    )
    config = rendered(client, site["id"])
    assert config.count("location / {") == 1
    assert "try_files $uri $uri/ =404;" not in config


def test_directory_password_writes_an_htpasswd_file(client, site):
    created = client.post(
        f"/api/sites/{site['id']}/dir-auth",
        json={"name": "Admin", "location": "/admin", "username": "ops", "password": "sekrit1"},
    )
    assert created.status_code == 200, created.text
    row = created.json()

    passwd = nginx.auth_file("extras.test", row["id"])
    assert passwd.is_file()
    body = passwd.read_text()
    assert body.startswith("ops:")
    assert "sekrit1" not in body  # hashed, never stored in the clear

    config = rendered(client, site["id"])
    assert 'auth_basic "Admin";' in config
    assert str(passwd) in config


def test_directory_password_minimum_length(client, site):
    response = client.post(
        f"/api/sites/{site['id']}/dir-auth",
        json={"name": "Admin", "location": "/admin", "username": "ops", "password": "short"},
    )
    assert response.status_code == 400


def test_deleting_a_site_takes_its_htpasswd_with_it(client, site):
    row = client.post(
        f"/api/sites/{site['id']}/dir-auth",
        json={"name": "Admin", "location": "/admin", "username": "ops", "password": "sekrit1"},
    ).json()
    passwd = nginx.auth_file("extras.test", row["id"])
    assert passwd.is_file()

    client.delete(f"/api/sites/{site['id']}")
    assert not passwd.exists()
    assert client.get(f"/api/sites/{site['id']}/dir-auth").status_code == 404


def test_upstream_pool_lives_in_its_own_file(client):
    pool = client.post(
        "/api/sites/upstreams", json={"name": "web-pool", "method": "least_conn"}
    ).json()
    client.post(f"/api/sites/upstreams/{pool['id']}/nodes", json={"address": "10.0.0.1:8080", "weight": 3})
    client.post(f"/api/sites/upstreams/{pool['id']}/nodes", json={"address": "10.0.0.2:8080", "backup": True})

    body = nginx.upstream_file("web-pool").read_text()
    assert "upstream web-pool {" in body
    assert "least_conn;" in body
    assert "server 10.0.0.1:8080 weight=3" in body
    assert "server 10.0.0.2:8080 weight=1 max_fails=3 fail_timeout=30s backup;" in body


def test_two_sites_can_share_one_pool(client):
    """Inlining the pool per vhost produced a duplicate upstream, which nginx rejects."""
    pool = client.post("/api/sites/upstreams", json={"name": "shared"}).json()
    client.post(f"/api/sites/upstreams/{pool['id']}/nodes", json={"address": "10.0.0.1:8080"})

    for name in ("lb-one.test", "lb-two.test"):
        created = client.post(
            "/api/sites", json={"name": name, "site_type": "balance", "upstream_name": "shared"}
        )
        assert created.status_code == 200, created.text
        config = rendered(client, created.json()["id"])
        assert "proxy_pass http://shared;" in config
        assert "upstream shared {" not in config  # it comes from the pool's own file


def test_an_emptied_pool_removes_its_file(client):
    pool = client.post("/api/sites/upstreams", json={"name": "drain"}).json()
    node = client.post(f"/api/sites/upstreams/{pool['id']}/nodes", json={"address": "10.0.0.1:80"}).json()
    assert nginx.upstream_file("drain").is_file()

    # An upstream block with no server line does not parse, so nothing is left behind.
    client.delete(f"/api/sites/upstreams/nodes/{node['id']}")
    assert not nginx.upstream_file("drain").exists()


def test_a_pool_in_use_cannot_be_deleted(client):
    pool = client.post("/api/sites/upstreams", json={"name": "busy"}).json()
    client.post(f"/api/sites/upstreams/{pool['id']}/nodes", json={"address": "10.0.0.1:80"})
    client.post("/api/sites", json={"name": "bound.test", "site_type": "balance", "upstream_name": "busy"})

    response = client.delete(f"/api/sites/upstreams/{pool['id']}")
    assert response.status_code == 400
    assert "bound.test" in response.json()["detail"]


def test_balanced_site_needs_a_pool(client):
    response = client.post("/api/sites", json={"name": "nopool.test", "site_type": "balance"})
    assert response.status_code == 400


@pytest.mark.parametrize("address", ["not a host", "10.0.0.1:99999x", "host;rm -rf /", ""])
def test_upstream_node_address_is_validated(client, address):
    pool = client.post("/api/sites/upstreams", json={"name": "guard"}).json()
    response = client.post(f"/api/sites/upstreams/{pool['id']}/nodes", json={"address": address})
    assert response.status_code == 400


def test_rewrite_library_is_listed_and_applied(client, site):
    listing = client.get("/api/sites/rewrite-templates").json()
    keys = {item["key"] for item in listing}
    assert {"wordpress", "laravel", "thinkphp", "spa"} <= keys

    template = client.get("/api/sites/rewrite-templates/wordpress").json()
    assert "try_files $uri $uri/ /index.php?$args;" in template["body"]

    assert client.get("/api/sites/rewrite-templates/nonsense").status_code == 404

    saved = client.post(f"/api/sites/{site['id']}/rewrite", json={"content": template["body"]})
    assert saved.status_code == 200
    assert nginx.rewrite_file("extras.test").read_text() == template["body"]


def test_a_rewrite_claiming_root_suppresses_the_default_location(client, site):
    client.post(
        f"/api/sites/{site['id']}/rewrite",
        json={"content": "location / { try_files $uri /index.html; }"},
    )
    config = rendered(client, site["id"])
    assert "try_files $uri $uri/ =404;" not in config
    assert config.count("include ") >= 1


def test_rewrite_include_is_globbed(client, site):
    """A plain include of a deleted file is fatal to all of nginx, not just one site."""
    config = rendered(client, site["id"])
    assert f"{nginx.rewrite_file('extras.test')}*;" in config


def test_hardening_fields_reach_the_vhost(client, site):
    response = client.patch(
        f"/api/sites/{site['id']}",
        json={
            "waf_enabled": True,
            "deny_extensions": "sql,bak",
            "anti_leech_enabled": True,
            "anti_leech_allow": "extras.test",
            "anti_leech_return": "404",
            "limit_req": 10,
            "limit_conn": 20,
            "limit_rate": 512,
            "client_max_body": "64m",
            "cache_enabled": True,
            "ip_deny": "198.51.100.7",
            "ip_allow": "10.0.0.0/8",
            "extra_headers": 'add_header X-Panel "slimpanel";',
            "hsts": True,
        },
    )
    assert response.status_code == 200, response.text

    config = rendered(client, site["id"])
    assert "sqlmap" in config  # the request filter
    assert r"location ~* \.(sql|bak)$" in config
    assert "valid_referers none blocked server_names extras.test;" in config
    assert "limit_req_zone $binary_remote_addr zone=sp_extras_test_req:10m rate=10r/s;" in config
    assert "limit_conn sp_extras_test_conn 20;" in config
    assert "limit_rate 512k;" in config
    assert "client_max_body_size 64m;" in config
    assert "deny 198.51.100.7;" in config
    assert "allow 10.0.0.0/8;" in config
    assert "deny all;" in config
    assert 'add_header X-Panel "slimpanel";' in config


def test_hsts_only_appears_with_ssl(client, site):
    client.patch(f"/api/sites/{site['id']}", json={"hsts": True})
    assert "Strict-Transport-Security" not in rendered(client, site["id"])


def test_app_site_proxies_to_its_bound_project_port(client):
    project = client.post(
        "/api/projects",
        json={"name": "api-app", "runtime": "node", "path": "", "command": "node server.js",
              "port": 4321, "autostart": False},
    )
    assert project.status_code == 200, project.text

    site = client.post(
        "/api/sites",
        json={"name": "app.test", "site_type": "node", "project_id": project.json()["id"]},
    ).json()
    assert "proxy_pass http://127.0.0.1:4321;" in rendered(client, site["id"])


def test_app_site_without_a_project_falls_back_to_3000(client):
    site = client.post("/api/sites", json={"name": "bare-app.test", "site_type": "node"}).json()
    assert "proxy_pass http://127.0.0.1:3000;" in rendered(client, site["id"])
