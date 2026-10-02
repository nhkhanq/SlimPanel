import json

from sqlmodel import select

from app.cli import main
from app.models import Site, User
from tests.aapanel_fixture import build


def args_for(panel_dir, cron_dir, *extra):
    return ["import-aapanel", "--panel-dir", str(panel_dir), "--cron-dir", str(cron_dir), *extra]


def test_inspect_prints_schema(tmp_path, capsys):
    panel_dir, cron_dir = build(tmp_path)
    assert main(["inspect-aapanel", "--panel-dir", str(panel_dir)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"]["sites"] == 9
    assert "where_hour" in payload["tables"]["crontab"]


def test_inspect_missing_panel_returns_error(tmp_path, capsys):
    assert main(["inspect-aapanel", "--panel-dir", str(tmp_path / "nope")]) == 1
    assert "aaPanel database not found" in capsys.readouterr().err


def test_dry_run_writes_nothing(tmp_path, capsys, session):
    panel_dir, cron_dir = build(tmp_path)
    assert main(args_for(panel_dir, cron_dir)) == 0

    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "+ php.test" in out
    assert session.exec(select(Site)).all() == []


def test_apply_imports(tmp_path, capsys, session):
    panel_dir, cron_dir = build(tmp_path)
    assert main(args_for(panel_dir, cron_dir, "--apply")) == 0

    assert "APPLIED" in capsys.readouterr().out
    assert len(session.exec(select(Site)).all()) == 7


def test_json_output(tmp_path, capsys):
    panel_dir, cron_dir = build(tmp_path)
    main(args_for(panel_dir, cron_dir, "--json"))

    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["site"]["import"] == 7
    assert payload["tables"]["sites"]


def test_create_user_and_set_password(capsys, session):
    assert main(["create-user", "ops", "ops-password-1"]) == 0
    assert main(["create-user", "ops", "again"]) == 1
    assert main(["set-password", "ops", "another-password"]) == 0
    assert main(["set-password", "ghost", "x"]) == 1

    assert session.exec(select(User).where(User.username == "ops")).first() is not None
