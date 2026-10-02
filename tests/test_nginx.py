from app.models import Site, SiteType
from app.services import nginx


def make_site(**overrides) -> Site:
    data = {
        "id": 1,
        "name": "example.com",
        "site_type": SiteType.static,
        "root": "/tmp/example.com",
        "run_path": "",
        "index_files": "index.html",
    }
    data.update(overrides)
    return Site(**data)


def test_static_site_has_no_php_or_proxy():
    conf = nginx.render_vhost(make_site(), ["example.com", "www.example.com"])
    assert "server_name example.com www.example.com;" in conf
    assert "fastcgi_pass" not in conf
    assert "proxy_pass" not in conf
    assert "try_files $uri $uri/ =404;" in conf


def test_php_site_renders_fastcgi():
    conf = nginx.render_vhost(
        make_site(site_type=SiteType.php, php_version="8.1"), ["example.com"]
    )
    assert "fastcgi_pass unix:/run/php/php8.1-fpm.sock;" in conf
    assert "/index.php?$query_string" in conf


def test_proxy_site_renders_upstream():
    conf = nginx.render_vhost(
        make_site(site_type=SiteType.proxy, proxy_target="http://127.0.0.1:3000"),
        ["api.example.com"],
    )
    assert "proxy_pass http://127.0.0.1:3000;" in conf
    assert "proxy_set_header X-Forwarded-Proto $scheme;" in conf


def test_ssl_block_only_when_enabled():
    plain = nginx.render_vhost(make_site(), ["example.com"])
    assert "listen 443" not in plain

    secured = nginx.render_vhost(make_site(ssl_enabled=True), ["example.com"])
    assert "listen 443 ssl;" in secured
    assert "ssl_certificate " in secured
    assert "return 301 https://$host$request_uri;" not in secured


def test_force_https_requires_ssl():
    conf = nginx.render_vhost(make_site(ssl_enabled=True, force_https=True), ["example.com"])
    assert "return 301 https://$host$request_uri;" in conf


def test_run_path_changes_document_root():
    site = make_site(run_path="public")
    assert nginx.document_root(site).endswith("/example.com/public")
    assert f"root {nginx.document_root(site)};" in nginx.render_vhost(site, ["example.com"])


def test_acme_challenge_location_always_present():
    conf = nginx.render_vhost(make_site(), ["example.com"])
    assert "location ^~ /.well-known/acme-challenge/" in conf


def test_write_vhost_creates_files():
    site = make_site(name="written.test")
    path = nginx.write_vhost(site, ["written.test"])
    assert path.exists()
    assert nginx.rewrite_file("written.test").exists()
    nginx.remove_vhost("written.test")
    assert not path.exists()


def test_set_enabled_parks_and_restores_config():
    site = make_site(name="toggle.test")
    nginx.write_vhost(site, ["toggle.test"])

    nginx.set_enabled("toggle.test", False)
    assert nginx.disabled_vhost_file("toggle.test").exists()
    assert not nginx.vhost_file("toggle.test").exists()

    nginx.set_enabled("toggle.test", True)
    assert nginx.vhost_file("toggle.test").exists()
    nginx.remove_vhost("toggle.test")
