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
    assert info["rows"]["sites"] == 5


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

    assert summary["site"]["import"] == 3
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

    assert set(sites) == {"php.test", "proxy.test", "static.test"}
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
    assert len(session.exec(select(Site)).all()) == 3
    assert len(session.exec(select(Database)).all()) == 2


def test_preview_endpoint(client, source):
    response = client.post(
        "/api/import/aapanel/preview",
        json={"panel_dir": str(source.panel_dir), "cron_dir": str(source.cron_dir)},
    )
    assert response.status_code == 200
    assert response.json()["summary"]["site"]["import"] == 3


def test_apply_endpoint(client, source):
    response = client.post(
        "/api/import/aapanel/apply",
        json={"panel_dir": str(source.panel_dir), "cron_dir": str(source.cron_dir)},
    )
    assert response.status_code == 200
    assert len(client.get("/api/sites").json()) == 3


def test_inspect_endpoint_requires_auth(anon, source):
    response = anon.post("/api/import/aapanel/inspect", json={"panel_dir": str(source.panel_dir)})
    assert response.status_code == 401
