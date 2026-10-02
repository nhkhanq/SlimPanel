import pytest

from app.errors import PanelError
from app.services.cron import validate_command, validate_schedule


@pytest.mark.parametrize("schedule", ["0 3 * * *", "*/5 * * * *", "0,30 1-5 * * 1"])
def test_valid_schedules(schedule):
    assert validate_schedule(schedule) == schedule


@pytest.mark.parametrize("schedule", ["", "0 3 * *", "0 3 * * * *", "0 3 * * $(id)"])
def test_invalid_schedules(schedule):
    with pytest.raises(PanelError):
        validate_schedule(schedule)


def test_command_rejects_newline_and_percent():
    assert validate_command(" echo hi ") == "echo hi"
    with pytest.raises(PanelError):
        validate_command("echo a\nrm -rf /")
    with pytest.raises(PanelError):
        validate_command("date +%s")


def test_create_job_appears_in_render(client):
    created = client.post(
        "/api/cron", json={"name": "nightly", "schedule": "0 3 * * *", "command": "echo hi"}
    )
    assert created.status_code == 200, created.text

    rendered = client.get("/api/cron/render").json()["content"]
    assert "0 3 * * * root echo hi" in rendered
    assert "Managed by SlimPanel" in rendered


def test_disabled_job_is_commented_out(client):
    job = client.post(
        "/api/cron", json={"name": "off", "schedule": "0 4 * * *", "command": "echo off"}
    ).json()
    client.patch(f"/api/cron/{job['id']}", json={"enabled": False})

    rendered = client.get("/api/cron/render").json()["content"]
    assert "# 0 4 * * * root echo off" in rendered


def test_invalid_schedule_rejected_by_api(client):
    response = client.post(
        "/api/cron", json={"name": "bad", "schedule": "not a schedule", "command": "echo"}
    )
    assert response.status_code == 400


def test_run_now_writes_log(client):
    job = client.post(
        "/api/cron", json={"name": "runner", "schedule": "0 5 * * *", "command": "echo ran"}
    ).json()

    result = client.post(f"/api/cron/{job['id']}/run")
    assert result.status_code == 200

    logs = client.get(f"/api/cron/{job['id']}/logs").json()["lines"]
    assert any("manual run" in line for line in logs)


def test_delete_job(client):
    job = client.post(
        "/api/cron", json={"name": "temp", "schedule": "0 6 * * *", "command": "echo temp"}
    ).json()
    assert client.delete(f"/api/cron/{job['id']}").status_code == 200
    assert client.get("/api/cron").json() == []


def test_sync_reports_target(client):
    client.post("/api/cron", json={"name": "s", "schedule": "0 7 * * *", "command": "echo s"})
    result = client.post("/api/cron/sync").json()
    assert result["installed"] is False
    assert result["reason"] == "dry-run"
