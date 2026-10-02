import pytest

from app.config import settings
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
    assert "listen 443 ssl" in secured
    assert "ssl_certificate " in secured
    assert "return 301 https://$host$request_uri;" not in secured


@pytest.mark.parametrize(
    "version,inline",
    [((1, 18, 0), True), ((1, 24, 0), True), ((1, 25, 1), False), ((1, 27, 0), False), (None, True)],
)
def test_http2_syntax_follows_the_nginx_version(monkeypatch, version, inline):
    monkeypatch.setattr(nginx, "version", lambda: version)
    assert nginx.uses_inline_http2() is inline

    conf = nginx.render_vhost(make_site(ssl_enabled=True), ["example.com"])
    if inline:
        assert "listen 443 ssl http2;" in conf
        assert "http2 on;" not in conf
    else:
        assert "listen 443 ssl;" in conf
        assert "http2 on;" in conf


def test_explicit_nginx_binary_wins(monkeypatch):
    monkeypatch.setattr(settings, "nginx_bin", "/opt/nginx/sbin/nginx")
    assert nginx.binary() == "/opt/nginx/sbin/nginx"


def test_binary_is_detected_when_set_to_auto(monkeypatch):
    monkeypatch.setattr(settings, "nginx_bin", "auto")
    assert nginx.binary().endswith("nginx")


def test_reload_uses_the_detected_binary(monkeypatch):
    monkeypatch.setattr(settings, "nginx_bin", "/opt/nginx/sbin/nginx")
    monkeypatch.setattr(settings, "nginx_reload_cmd", "")
    assert "/opt/nginx/sbin/nginx" in nginx.reload_config().output


def test_rewrite_root_detection():
    site = make_site(name="rewritten.test")
    nginx.rewrite_file(site.name).parent.mkdir(parents=True, exist_ok=True)

    nginx.rewrite_file(site.name).write_text("location /api { return 404; }")
    assert nginx.rewrite_defines_root(site.name) is False

    nginx.rewrite_file(site.name).write_text("location / {\n try_files $uri /index.html;\n}")
    assert nginx.rewrite_defines_root(site.name) is True

    conf = nginx.render_vhost(site, ["rewritten.test"])
    assert "try_files $uri $uri/ =404;" not in conf
    # Globbed so a deleted rewrite file cannot take all of nginx down.
    assert "rewritten.test.conf*;" in conf
    nginx.rewrite_file(site.name).unlink()


def test_proxy_site_keeps_its_own_root_location_over_a_rewrite():
    site = make_site(name="proxied.test", site_type=SiteType.proxy, proxy_target="http://127.0.0.1:7000")
    nginx.rewrite_file(site.name).parent.mkdir(parents=True, exist_ok=True)
    nginx.rewrite_file(site.name).write_text("location / { try_files $uri /index.html; }")

    conf = nginx.render_vhost(site, ["proxied.test"])
    assert "proxy_pass http://127.0.0.1:7000;" in conf
    assert "proxied.test.conf;" not in conf
    nginx.rewrite_file(site.name).unlink()


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
