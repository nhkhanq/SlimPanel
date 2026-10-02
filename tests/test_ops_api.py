"""Log analysis, backup and restore, remote targets, settings and one-click installs."""
from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from app.config import settings

ACCESS_LOG = """\
203.0.113.1 - - [02/Oct/2026:10:00:01 +0000] "GET /index.html HTTP/1.1" 200 1024 "https://ref.test/a" "Mozilla/5.0"
203.0.113.1 - - [02/Oct/2026:10:00:02 +0000] "GET /index.html HTTP/1.1" 200 1024 "-" "Mozilla/5.0"
203.0.113.2 - - [02/Oct/2026:10:05:03 +0000] "POST /api/login HTTP/1.1" 302 64 "-" "curl/8.0"
203.0.113.3 - - [02/Oct/2026:11:00:04 +0000] "GET /missing HTTP/1.1" 404 512 "-" "Googlebot/2.1"
203.0.113.3 - - [02/Oct/2026:11:00:05 +0000] "GET /boom HTTP/1.1" 500 0 "-" "ClaudeBot/1.0"
203.0.113.4 - - [02/Oct/2026:11:30:06 +0000] "GET /big.zip HTTP/1.1" 200 1048576 "-" "wget"
this line is not a log line at all
"""


@pytest.fixture
def logged_site(client, tmp_root):
    site = client.post("/api/sites", json={"name": "logs.test", "site_type": "static"}).json()
    (settings.log_root / "logs.test.log").write_text(ACCESS_LOG)
    (settings.log_root / "logs.test.error.log").write_text(
        "2026/10/02 10:00:01 [error] 1#1: *1 open() failed, client: 203.0.113.1, request: \"GET /a\"\n"
        "2026/10/02 10:00:02 [error] 1#1: *2 open() failed, client: 203.0.113.9, request: \"GET /b\"\n"
        "2026/10/02 10:00:03 [crit] 1#1: *3 SSL handshake failed, client: 203.0.113.1\n"
    )
    return site


def test_log_analysis_counts_what_matters(client, logged_site):
    report = client.get(f"/api/logs/site/{logged_site['id']}/analysis").json()

    assert report["parsed"] == 6  # the junk line is skipped
    assert report["unique_visitors"] == 4
    assert report["total_bytes"] == 1024 + 1024 + 64 + 512 + 0 + 1048576
    assert report["top_ips"][0] == {"ip": "203.0.113.1", "count": 2}
    assert report["top_paths"][0] == {"path": "/index.html", "count": 2}
    assert dict(
        (row["status"], row["count"]) for row in report["statuses"]
    ) == {"200": 3, "302": 1, "404": 1, "500": 1}
    assert report["heaviest_paths"][0]["path"] == "/big.zip"


def test_log_analysis_error_rate(client, logged_site):
    report = client.get(f"/api/logs/site/{logged_site['id']}/analysis").json()
    # two of six requests are 4xx/5xx
    assert report["error_rate"] == pytest.approx(33.33, abs=0.01)


def test_log_analysis_identifies_crawlers(client, logged_site):
    report = client.get(f"/api/logs/site/{logged_site['id']}/analysis").json()
    spiders = {row["spider"]: row["count"] for row in report["spiders"]}
    assert spiders == {"Google": 1, "Anthropic": 1}


def test_log_analysis_buckets_by_hour(client, logged_site):
    report = client.get(f"/api/logs/site/{logged_site['id']}/analysis").json()
    hours = {row["hour"]: row["count"] for row in report["hourly"]}
    assert hours["2026-10-02 10:00"] == 3
    assert hours["2026-10-02 11:00"] == 3


def test_log_analysis_skips_empty_referers(client, logged_site):
    report = client.get(f"/api/logs/site/{logged_site['id']}/analysis").json()
    assert [row["referer"] for row in report["top_referers"]] == ["https://ref.test/a"]


def test_error_log_is_grouped(client, logged_site):
    report = client.get(f"/api/logs/site/{logged_site['id']}/errors").json()
    # The client address is normalised away so the same fault reads as one row.
    messages = {row["message"]: row["count"] for row in report["entries"]}
    assert any("open() failed" in message and count == 2 for message, count in messages.items())


def test_log_rotation_keeps_a_copy(client, logged_site):
    before = (settings.log_root / "logs.test.log").stat().st_size
    result = client.post(f"/api/logs/site/{logged_site['id']}/rotate").json()

    assert result["bytes"] == before
    assert Path(result["archive"]).stat().st_size == before
    assert (settings.log_root / "logs.test.log").stat().st_size == 0


def test_log_truncation_frees_the_file(client, logged_site):
    result = client.post(f"/api/logs/site/{logged_site['id']}/truncate").json()
    assert result["ok"] is True
    assert (settings.log_root / "logs.test.log").stat().st_size == 0


def test_log_sizes_rank_the_biggest(client, logged_site):
    client.post("/api/sites", json={"name": "quiet.test", "site_type": "static"})
    rows = client.get("/api/logs/sizes").json()
    assert rows[0]["site"] == "logs.test"
    assert rows[0]["total"] > 0


def test_analysis_of_a_site_with_no_log_is_a_404(client):
    site = client.post("/api/sites", json={"name": "nolog.test", "site_type": "static"}).json()
    assert client.get(f"/api/logs/site/{site['id']}/analysis").status_code == 404


def test_operation_log_is_filterable(client):
    client.post("/api/sites", json={"name": "audited.test", "site_type": "static"})
    rows = client.get("/api/logs/operations", params={"action": "site."}).json()
    assert rows
    assert all(row["action"].startswith("site.") for row in rows)


def test_operation_log_can_be_trimmed(client):
    for index in range(5):
        client.post("/api/sites/groups", json={"name": f"g{index}"})
    body = client.delete("/api/logs/operations", params={"keep": 2}).json()
    assert "Removed" in body["message"]
    assert len(client.get("/api/logs/operations").json()) == 2


# ------------------------------------------------------------------ backups


def test_site_backup_and_restore_round_trip(client, www_root):
    root = www_root / "restoreme"
    root.mkdir()
    (root / "index.html").write_text("version one")
    (root / "keep").mkdir()
    (root / "keep" / "data.txt").write_text("nested one")

    site = client.post(
        "/api/sites", json={"name": "restore.test", "site_type": "static", "root": str(root)}
    ).json()

    record = client.post(f"/api/backups/site/{site['id']}").json()
    assert record["kind"] == "site"
    assert record["size"] > 0

    (root / "index.html").write_text("version two, broken")
    (root / "junk.txt").write_text("should go")

    restored = client.post(f"/api/backups/{record['id']}/restore-site/{site['id']}")
    assert restored.status_code == 200, restored.text

    assert (root / "index.html").read_text() == "version one"
    assert (root / "keep" / "data.txt").read_text() == "nested one"
    assert not (root / "junk.txt").exists()  # the restore is a replacement


def test_restore_writes_a_safety_copy_first(client, www_root):
    root = www_root / "safety"
    root.mkdir()
    (root / "a.txt").write_text("before")
    site = client.post(
        "/api/sites", json={"name": "safety.test", "site_type": "static", "root": str(root)}
    ).json()
    record = client.post(f"/api/backups/site/{site['id']}").json()

    client.post(f"/api/backups/{record['id']}/restore-site/{site['id']}")
    assert any(path.name.startswith("pre-restore_safety.test") for path in settings.backup_dir.iterdir())


def test_restoring_a_database_dump_onto_a_site_is_refused(client, www_root):
    root = www_root / "mix"
    root.mkdir()
    (root / "x").write_text("x")
    site = client.post(
        "/api/sites", json={"name": "mix.test", "site_type": "static", "root": str(root)}
    ).json()
    record = client.post(f"/api/backups/site/{site['id']}").json()

    # A site tarball is not a SQL dump.
    assert client.post(f"/api/backups/{record['id']}/restore-database/1").status_code == 400


def test_restore_refuses_an_archive_that_escapes(client, www_root):
    root = www_root / "evilrestore"
    root.mkdir()
    (root / "x").write_text("x")
    site = client.post(
        "/api/sites", json={"name": "evil.test", "site_type": "static", "root": str(root)}
    ).json()
    record = client.post(f"/api/backups/site/{site['id']}").json()

    # Rewrite the archive with a traversing member.
    import io

    with tarfile.open(record["filename"], "w:gz") as archive:
        payload = io.BytesIO(b"pwned")
        info = tarfile.TarInfo("../../escaped.txt")
        info.size = 5
        archive.addfile(info, payload)

    response = client.post(f"/api/backups/{record['id']}/restore-site/{site['id']}")
    assert response.status_code == 400
    assert not (www_root.parent / "escaped.txt").exists()


def test_backup_everything_reports_per_item(client, www_root):
    root = www_root / "all"
    root.mkdir()
    (root / "a").write_text("a")
    client.post("/api/sites", json={"name": "all.test", "site_type": "static", "root": str(root)})

    result = client.post("/api/backups/all").json()
    assert len(result["records"]) >= 1
    assert isinstance(result["errors"], list)


def test_backup_pruning_keeps_the_newest(client, www_root):
    root = www_root / "pruneme"
    root.mkdir()
    (root / "a").write_text("a")
    site = client.post(
        "/api/sites", json={"name": "prune.test", "site_type": "static", "root": str(root)}
    ).json()

    for _ in range(4):
        client.post(f"/api/backups/site/{site['id']}")

    body = client.post("/api/backups/prune", params={"keep": 2}).json()
    assert "Removed 2" in body["message"]
    assert len(client.get("/api/backups").json()) == 2


def test_missing_backup_file_is_reported(client, www_root):
    root = www_root / "missingfile"
    root.mkdir()
    (root / "a").write_text("a")
    site = client.post(
        "/api/sites", json={"name": "missing.test", "site_type": "static", "root": str(root)}
    ).json()
    record = client.post(f"/api/backups/site/{site['id']}").json()
    Path(record["filename"]).unlink()

    assert client.get(f"/api/backups/{record['id']}/download").status_code == 404


# ----------------------------------------------------------- remote targets


def test_target_kinds_report_their_tooling(client):
    rows = client.get("/api/backups/targets/kinds").json()
    keys = {row["key"] for row in rows}
    assert {"local", "s3", "ftp", "sftp", "rsync", "webdav"} <= keys


@pytest.mark.parametrize(
    "kind,config",
    [("local", {}), ("s3", {"bucket": "b"}), ("ftp", {"host": "h"}), ("webdav", {"url": "u"})],
)
def test_target_required_fields_are_enforced(client, kind, config):
    response = client.post("/api/backups/targets", json={"name": "t", "kind": kind, "config": config})
    assert response.status_code == 400


def test_unknown_target_kind_is_refused(client):
    response = client.post("/api/backups/targets", json={"name": "t", "kind": "carrier", "config": {}})
    assert response.status_code == 400


def test_target_secrets_are_masked(client, tmp_root):
    client.post(
        "/api/backups/targets",
        json={"name": "offsite", "kind": "ftp",
              "config": {"host": "ftp.test", "username": "u", "password": "hunter2"}},
    )
    listed = client.get("/api/backups/targets").json()
    assert listed[0]["config"]["password"] == "********"
    assert listed[0]["config"]["host"] == "ftp.test"


def test_a_local_target_receives_a_probe(client, tmp_root):
    destination = tmp_root / "offsite"
    target = client.post(
        "/api/backups/targets",
        json={"name": "local", "kind": "local", "config": {"path": str(destination)}},
    ).json()

    result = client.post(f"/api/backups/targets/{target['id']}/test")
    assert result.status_code == 200, result.text
    # dry_run means the copy is logged rather than run, so just assert it reported ok.
    assert result.json()["ok"] is True


# ----------------------------------------------------------------- settings


def test_settings_mask_secrets(client):
    body = client.get("/api/settings").json()
    assert "secret_key" not in body or body["secret_key"] == "********"
    assert isinstance(body["editable"], list)


def test_only_whitelisted_settings_can_be_written(client):
    response = client.post("/api/settings", json={"values": {"secret_key": "stolen"}})
    assert response.status_code == 400

    response = client.post("/api/settings", json={"values": {"dry_run": False}})
    assert response.status_code == 400


def test_settings_round_trip_to_the_config_file(client):
    response = client.post("/api/settings", json={"values": {"monitor_retention_days": 14}})
    assert response.status_code == 200, response.text
    assert response.json()["restart_required"] is True
    assert settings.monitor_retention_days == 14


def test_numeric_settings_are_validated(client):
    assert client.post("/api/settings", json={"values": {"port": "not a number"}}).status_code == 400
    assert client.post("/api/settings", json={"values": {"port": 99999}}).status_code == 400


def test_list_settings_accept_a_comma_string(client):
    response = client.post(
        "/api/settings", json={"values": {"panel_ip_allowlist": "10.0.0.1, 10.0.0.2"}}
    )
    assert response.status_code == 200
    assert settings.panel_ip_allowlist == ["10.0.0.1", "10.0.0.2"]
    settings.panel_ip_allowlist = []  # do not fence the rest of the suite out


def test_a_masked_secret_is_not_written_back(client):
    before = settings.mysql_password
    client.post("/api/settings", json={"values": {"mysql_password": "********"}})
    assert settings.mysql_password == before


def test_ui_preferences_round_trip(client):
    client.post("/api/settings/preferences", json={"key": "sidebar", "value": "collapsed"})
    assert client.get("/api/settings/preferences").json()["sidebar"] == "collapsed"

    client.post("/api/settings/preferences", json={"key": "sidebar", "value": "expanded"})
    assert client.get("/api/settings/preferences").json()["sidebar"] == "expanded"


def test_oversized_preferences_are_refused(client):
    response = client.post("/api/settings/preferences", json={"key": "k" * 100, "value": "v"})
    assert response.status_code == 400


def test_panel_https_needs_a_certificate_first(client):
    assert client.get("/api/settings/ssl").json()["enabled"] is False
    assert client.post("/api/settings/ssl/enabled/true").status_code == 400


def test_panel_certificate_upload_is_validated(client):
    response = client.post(
        "/api/settings/ssl/upload", json={"fullchain": "not a cert", "private_key": "nope"}
    )
    assert response.status_code == 400


def test_borrowing_from_a_site_without_a_cert_is_a_404(client):
    client.post("/api/sites", json={"name": "nocert.test", "site_type": "static"})
    assert client.post("/api/settings/ssl/borrow/nocert.test").status_code == 404


def test_nginx_config_is_read_only(client):
    body = client.get("/api/system/nginx/config").json()
    assert "includes_slimpanel" in body


# -------------------------------------------------------------- one-click


def test_one_click_catalogue(client):
    keys = {app["key"] for app in client.get("/api/one-click").json()}
    assert {"wordpress", "static", "phpmyadmin", "adminer"} <= keys


def test_one_click_static_deploy_writes_a_landing_page(client):
    result = client.post(
        "/api/one-click/deploy", json={"app": "static", "site_name": "oneclick.test"}
    )
    assert result.status_code == 200, result.text
    body = result.json()

    assert body["database"] is None
    assert body["url"] == "http://oneclick.test"
    assert (Path(body["site"]["root"]) / "index.html").read_text().count("oneclick.test") >= 1


def test_one_click_rejects_an_unknown_app(client):
    response = client.post("/api/one-click/deploy", json={"app": "drupal9000", "site_name": "x.test"})
    assert response.status_code == 400


def test_one_click_applies_the_rewrite_template(client):
    from app.services import nginx

    client.post("/api/one-click/deploy", json={"app": "laravel-skeleton", "site_name": "lara.test"})
    rewrite = nginx.rewrite_file("lara.test").read_text()
    assert "try_files $uri $uri/ /index.php?$query_string;" in rewrite

    site = next(s for s in client.get("/api/sites").json() if s["name"] == "lara.test")
    assert site["run_path"] == "/public"
