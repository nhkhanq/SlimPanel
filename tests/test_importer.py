import pytest
from sqlmodel import select

from app.models import CronJob, Database, Site, SiteType
from app.services import importer, nginx
from tests.aapanel_fixture import build


@pytest.fixture
def source(tmp_path):
    panel_dir, cron_dir = build(tmp_path)
    return importer.Source(panel_dir=panel_dir, cron_dir=cron_dir)


def test_missing_database_is_reported(tmp_path):
    bad = importer.Source(panel_dir=tmp_path / "nope")
    with pytest.raises(Exception):
        bad.check()


def test_inspect_lists_tables_and_counts(source):
    info = importer.inspect(source)
    assert "sites" in info["tables"]
    assert "name" in info["tables"]["sites"]
    assert info["rows"]["sites"] == 9


def test_parse_php_vhost(source):
    conf = (source.vhost_dir / "php.test.conf").read_text()
    parsed = importer.parse_vhost(conf)
    assert parsed["php_version"] == "7.4"
    assert parsed["root"] == "/www/wwwroot/php.test/public"
    assert parsed["domains"] == ["php.test", "www.php.test"]
    assert parsed["ssl"] is True
    assert parsed["force_https"] is True
    assert parsed["proxy_target"] == ""


def test_parse_proxy_vhost(source):
    parsed = importer.parse_vhost((source.vhost_dir / "proxy.test.conf").read_text())
    assert parsed["proxy_target"] == "http://127.0.0.1:3000"
    assert importer.site_type_of(parsed) == SiteType.proxy


def test_commented_ssl_is_ignored(source):
    parsed = importer.parse_vhost((source.vhost_dir / "static.test.conf").read_text())
    assert parsed["ssl"] is False
    assert importer.site_type_of(parsed) == SiteType.static


@pytest.mark.parametrize(
    "row,expected",
    [
        ({"type": "day", "where1": "", "where_hour": 3, "where_minute": 30}, "30 3 * * *"),
        ({"type": "day-n", "where1": "2", "where_hour": 1, "where_minute": 0}, "0 1 */2 * *"),
        ({"type": "hour", "where1": "", "where_hour": 0, "where_minute": 15}, "15 * * * *"),
        ({"type": "hour-n", "where1": "6", "where_hour": 0, "where_minute": 5}, "5 */6 * * *"),
        ({"type": "minute-n", "where1": "5", "where_hour": 0, "where_minute": 0}, "*/5 * * * *"),
        ({"type": "week", "where1": "1", "where_hour": 2, "where_minute": 0}, "0 2 * * 1"),
        ({"type": "month", "where1": "15", "where_hour": 4, "where_minute": 0}, "0 4 15 * *"),
    ],
)
def test_cron_schedule_conversion(row, expected):
    assert importer.cron_schedule(row) == expected


def test_plan_classifies_everything(session, source):
    report = importer.plan(session, source)
    summary = report.summary()

    assert summary["site"]["import"] == 7
    assert summary["site"]["skip"] == 2
    assert summary["database"]["import"] == 2
    assert summary["database"]["skip"] == 2
    assert summary["cron"]["import"] == 3
    assert summary["cron"]["skip"] == 1


def test_plan_skip_reasons(session, source):
    skipped = {item.name: item.reason for item in report_skips(session, source)}
    assert "vhost not found" in skipped["missing.test"]
    assert "mongodb" in skipped["mongo_db"]
    assert "script not found" in skipped["broken job"]


def report_skips(session, source):
    return [item for item in importer.plan(session, source).items if item.action == "skip"]


def test_plan_does_not_write_anything(session, source):
    importer.plan(session, source)
    assert session.exec(select(Site)).all() == []
    assert not nginx.vhost_file("php.test").exists()


def test_apply_imports_sites(session, source):
    importer.apply(session, source)
    sites = {site.name: site for site in session.exec(select(Site)).all()}

    assert set(sites) == {
        "php.test",
        "proxy.test",
        "static.test",
        "node.test",
        "moved.test",
        "spa.test",
        "mixed.test",
    }
    php = sites["php.test"]
    assert php.site_type == SiteType.php
    assert php.php_version == "7.4"
    assert php.root == "/www/wwwroot/php.test"
    assert php.run_path == "public"
    assert php.ssl_enabled is True
    assert php.force_https is True
    assert php.note == "php site"

    proxy = sites["proxy.test"]
    assert proxy.site_type == SiteType.proxy
    assert proxy.proxy_target == "http://127.0.0.1:3000"


def test_imported_sites_are_parked_by_default(session, source):
    importer.apply(session, source)
    assert nginx.disabled_vhost_file("php.test").exists()
    assert not nginx.vhost_file("php.test").exists()
    assert session.exec(select(Site).where(Site.name == "php.test")).first().enabled is False


def test_apply_with_activate_serves_sites(session, source):
    importer.apply(session, source, activate=True)
    assert nginx.vhost_file("php.test").exists()
    assert session.exec(select(Site).where(Site.name == "php.test")).first().enabled is True


def test_certificates_are_copied(session, source):
    importer.apply(session, source)
    cert, key = nginx.cert_paths("php.test")
    assert cert.read_text() == "FULLCHAIN"
    assert key.read_text() == "PRIVKEY"
    assert oct(key.stat().st_mode)[-3:] == "600"


def test_rewrite_rules_are_copied(session, source):
    importer.apply(session, source)
    assert "return 301 /new;" in nginx.rewrite_file("php.test").read_text()


def test_domains_come_from_the_database(session, source):
    importer.apply(session, source)
    site = session.exec(select(Site).where(Site.name == "php.test")).first()
    from app.services.sites import domain_names

    assert domain_names(session, site.id) == ["php.test", "www.php.test"]


def test_databases_are_registered_not_created(session, source):
    importer.apply(session, source)
    rows = {row.name: row for row in session.exec(select(Database)).all()}
    assert set(rows) == {"app_db", "logs_db"}
    assert rows["app_db"].password == "s3cret"
    assert rows["app_db"].note == "main database"


def test_cron_jobs_are_imported_with_copied_scripts(session, source):
    importer.apply(session, source)
    jobs = {job.name: job for job in session.exec(select(CronJob)).all()}

    assert jobs["nightly log rotate"].schedule == "30 3 * * *"
    assert jobs["nightly log rotate"].enabled is True
    assert jobs["every 5 minutes"].schedule == "*/5 * * * *"

    script = jobs["nightly log rotate"].command.split()[-1]
    assert "echo nightly backup" in open(script).read()


def test_aapanel_dependent_cron_is_disabled(session, source):
    importer.apply(session, source)
    job = session.exec(select(CronJob).where(CronJob.name == "aapanel site backup")).first()
    assert job.enabled is False


def test_apply_is_idempotent(session, source):
    importer.apply(session, source)
    second = importer.apply(session, source)

    assert second.summary()["site"].get("import") is None
    assert len(session.exec(select(Site)).all()) == 7
    assert len(session.exec(select(Database)).all()) == 2


def test_preview_endpoint(client, source):
    response = client.post(
        "/api/import/aapanel/preview",
        json={"panel_dir": str(source.panel_dir), "cron_dir": str(source.cron_dir)},
    )
    assert response.status_code == 200
    assert response.json()["summary"]["site"]["import"] == 7


def test_apply_endpoint(client, source):
    response = client.post(
        "/api/import/aapanel/apply",
        json={"panel_dir": str(source.panel_dir), "cron_dir": str(source.cron_dir)},
    )
    assert response.status_code == 200
    assert len(client.get("/api/sites").json()) == 7


def test_inspect_endpoint_requires_auth(anon, source):
    response = anon.post("/api/import/aapanel/inspect", json={"panel_dir": str(source.panel_dir)})
    assert response.status_code == 401


def test_proxy_defined_in_an_included_file_is_found(session, source):
    importer.apply(session, source)
    site = session.exec(select(Site).where(Site.name == "node.test")).first()
    assert site.site_type == SiteType.proxy
    assert site.proxy_target == "http://127.0.0.1:5000"


def test_include_resolution_stays_inside_the_panel_directory(tmp_path, source):
    outside = tmp_path / "outside.conf"
    outside.write_text("location / { proxy_pass http://127.0.0.1:9999; }")
    conf = f"server {{ server_name x.test; root /tmp/x; include {outside}; }}"

    parsed = importer.parse_vhost(conf, source.panel_dir)
    assert parsed["proxy_target"] == ""


def test_root_outside_the_recorded_path_is_kept_whole(session, source):
    importer.apply(session, source)
    site = session.exec(select(Site).where(Site.name == "moved.test")).first()
    assert site.root == "/srv/app/dist"
    assert site.run_path == ""


def test_run_path_is_split_only_when_nested(session, source):
    importer.apply(session, source)
    php = session.exec(select(Site).where(Site.name == "php.test")).first()
    assert php.root == "/www/wwwroot/php.test"
    assert php.run_path == "public"


def test_non_root_proxy_locations_are_carried_over(session, source):
    report = importer.apply(session, source)
    site = session.exec(select(Site).where(Site.name == "mixed.test")).first()

    assert site.site_type == SiteType.static
    assert "proxy_pass http://127.0.0.1:9000;" in site.extra_config
    assert "proxy_pass http://127.0.0.1:9000;" in nginx.disabled_vhost_file("mixed.test").read_text()

    item = next(i for i in report.of("site") if i.name == "mixed.test")
    assert "extra proxy locations carried over" in item.reason


def test_spa_rewrite_does_not_duplicate_the_root_location(session, source):
    importer.apply(session, source)
    conf = nginx.disabled_vhost_file("spa.test").read_text()

    assert conf.count("location / {") == 0
    assert "include" in conf and "spa.test.conf" in conf
    assert "try_files" in nginx.rewrite_file("spa.test").read_text()


def test_force_https_survives_a_round_trip(session, source):
    importer.apply(session, source)
    conf = nginx.disabled_vhost_file("spa.test").read_text()
    reparsed = importer.parse_vhost(conf)

    assert reparsed["force_https"] is True
    assert reparsed["ssl"] is True


def test_commented_https_redirect_is_not_force_https():
    conf = "server { server_name a.test;\n#    return 301 https://$host$request_uri;\n}"
    assert importer.parse_vhost(conf)["force_https"] is False


def test_inspect_reports_whether_a_mysql_root_password_is_recorded(source):
    info = importer.inspect(source)
    assert info["mysql_root_recorded"] is True


def test_stale_database_records_are_skipped(session, source, monkeypatch):
    from app.config import settings
    from app.services import mysql

    monkeypatch.setattr(settings, "dry_run", False)
    monkeypatch.setattr(mysql, "server_available", lambda: True)
    monkeypatch.setattr(mysql, "list_server_databases", lambda: ["app_db"])

    report = importer.plan(session, source)
    actions = {item.name: (item.action, item.reason) for item in report.of("database")}

    assert actions["app_db"][0] == "import"
    assert actions["logs_db"][0] == "skip"
    assert "stale aaPanel record" in actions["logs_db"][1]


def test_databases_are_imported_when_mysql_is_unreachable(session, source, monkeypatch):
    from app.config import settings
    from app.services import mysql

    monkeypatch.setattr(settings, "dry_run", False)
    monkeypatch.setattr(mysql, "server_available", lambda: False)

    report = importer.plan(session, source)
    assert report.summary()["database"]["import"] == 2


def test_dry_run_does_not_query_mysql(session, source, monkeypatch):
    from app.services import mysql

    def explode():
        raise AssertionError("MySQL must not be queried during a dry run")

    monkeypatch.setattr(mysql, "server_available", explode)
    assert importer.plan(session, source).summary()["database"]["import"] == 2
