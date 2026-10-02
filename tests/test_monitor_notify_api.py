"""Sampling, history, alert rules and their delivery."""
from __future__ import annotations

from datetime import timedelta

import pytest
from sqlmodel import Session, select

from app.db import engine
from app.models import MonitorSample, NotifyChannel, utcnow
from app.services import monitor, notify


def test_a_sample_captures_the_usual_metrics(client):
    response = client.post("/api/monitor/sample")
    assert response.status_code == 200, response.text
    body = response.json()
    assert 0 <= body["cpu"] <= 100
    assert 0 <= body["memory"] <= 100
    assert body["processes"] > 0


def test_history_is_thinned_to_the_requested_point_count(client):
    with Session(engine) as session:
        base = utcnow()
        for index in range(600):
            session.add(
                MonitorSample(taken_at=base - timedelta(minutes=index), cpu=index % 100, memory=50)
            )
        session.commit()

    body = client.get("/api/monitor/history", params={"hours": 24, "points": 100}).json()
    assert body["total"] > body["count"]
    assert body["count"] <= 120  # thinning is approximate, never unbounded


def test_history_only_covers_the_window(client):
    with Session(engine) as session:
        session.add(MonitorSample(taken_at=utcnow() - timedelta(days=5), cpu=99))
        session.add(MonitorSample(taken_at=utcnow(), cpu=11))
        session.commit()

    body = client.get("/api/monitor/history", params={"hours": 1}).json()
    assert [round(s["cpu"]) for s in body["samples"]] == [11]


def test_summary_reports_min_max_average(client):
    with Session(engine) as session:
        for value in (10.0, 20.0, 60.0):
            session.add(MonitorSample(cpu=value, memory=value, load1=value / 10, disk_percent=value))
        session.commit()

    body = client.get("/api/monitor/summary", params={"hours": 1}).json()
    assert body["count"] == 3
    assert body["cpu"] == {"avg": 30.0, "max": 60.0, "min": 10.0}


def test_summary_of_an_empty_window_is_not_an_error(client):
    body = client.get("/api/monitor/summary", params={"hours": 1}).json()
    assert body["count"] == 0


def test_pruning_drops_only_old_samples(client):
    with Session(engine) as session:
        session.add(MonitorSample(taken_at=utcnow() - timedelta(days=40), cpu=1))
        session.add(MonitorSample(taken_at=utcnow(), cpu=2))
        session.commit()

    removed = client.post("/api/monitor/prune", params={"days": 30}).json()
    assert "Removed 1" in removed["message"]

    with Session(engine) as session:
        assert len(session.exec(select(MonitorSample)).all()) == 1


def test_clearing_history_empties_the_table(client):
    client.post("/api/monitor/sample")
    body = client.delete("/api/monitor").json()
    assert "Cleared" in body["message"]
    assert client.get("/api/monitor/history").json()["total"] == 0


def test_sampler_is_off_in_dry_run(client):
    # Sampling shells out to nothing, but dry-run means "touch nothing", so the
    # background thread stays down and the UI should say so.
    assert monitor.start() is False
    assert client.get("/api/monitor/status").json()["running"] is False


@pytest.mark.parametrize(
    "kind,config",
    [
        ("webhook", {}),
        ("telegram", {"token": "x"}),
        ("email", {"host": "smtp.test", "port": "587"}),
    ],
)
def test_channel_required_fields_are_enforced(client, kind, config):
    response = client.post("/api/notify/channels", json={"name": "c", "kind": kind, "config": config})
    assert response.status_code == 400


def test_unknown_channel_kind_is_refused(client):
    response = client.post(
        "/api/notify/channels", json={"name": "c", "kind": "carrier-pigeon", "config": {}}
    )
    assert response.status_code == 400


def test_channel_secrets_are_masked_in_listings(client):
    client.post(
        "/api/notify/channels",
        json={
            "name": "mail",
            "kind": "email",
            "config": {"host": "smtp.test", "port": "587", "username": "u",
                       "password": "super-secret", "to": "ops@test"},
        },
    )
    listed = client.get("/api/notify/channels").json()
    assert listed[0]["config"]["password"] == "********"
    assert listed[0]["config"]["host"] == "smtp.test"


def test_a_masked_secret_is_not_written_back(client):
    created = client.post(
        "/api/notify/channels",
        json={"name": "hook", "kind": "webhook", "config": {"url": "http://a.test/hook"}},
    ).json()

    client.patch(
        f"/api/notify/channels/{created['id']}",
        json={"config": {"url": "http://b.test/hook", "password": "********"}},
    )
    with Session(engine) as session:
        channel = session.get(NotifyChannel, created["id"])
        assert "b.test" in channel.config
        assert "********" not in channel.config


def test_deleting_a_channel_unbinds_its_rules(client):
    channel = client.post(
        "/api/notify/channels",
        json={"name": "hook", "kind": "webhook", "config": {"url": "http://a.test/hook"}},
    ).json()
    rule = client.post(
        "/api/notify/rules",
        json={"name": "cpu", "metric": "cpu", "threshold": 90, "channel_id": channel["id"]},
    ).json()

    client.delete(f"/api/notify/channels/{channel['id']}")
    assert client.get("/api/notify/rules").json()[0]["channel_id"] is None
    assert rule["channel_id"] == channel["id"]


@pytest.mark.parametrize("metric", ["vibes", ""])
def test_rule_metric_is_restricted(client, metric):
    response = client.post(
        "/api/notify/rules", json={"name": "r", "metric": metric, "threshold": 1}
    )
    assert response.status_code == 400


def test_rule_operator_is_restricted(client):
    response = client.post(
        "/api/notify/rules", json={"name": "r", "metric": "cpu", "operator": "~=", "threshold": 1}
    )
    assert response.status_code == 400


def test_a_rule_fires_against_the_newest_sample(client):
    client.post(
        "/api/notify/rules",
        json={"name": "always", "metric": "cpu", "operator": ">", "threshold": -1},
    )
    with Session(engine) as session:
        session.add(MonitorSample(cpu=42.0))
        session.commit()

    fired = client.post("/api/notify/evaluate").json()
    assert fired["fired"] == 1

    events = client.get("/api/notify/events").json()
    assert "42" in events[0]["body"]
    assert events[0]["delivered"] is False  # no channel configured
    assert "no enabled channel" in events[0]["detail"]


def test_a_rule_that_does_not_match_stays_quiet(client):
    client.post(
        "/api/notify/rules",
        json={"name": "never", "metric": "cpu", "operator": ">", "threshold": 1000},
    )
    with Session(engine) as session:
        session.add(MonitorSample(cpu=5.0))
        session.commit()

    assert client.post("/api/notify/evaluate").json()["fired"] == 0


def test_cooldown_suppresses_a_repeat(client):
    client.post(
        "/api/notify/rules",
        json={"name": "noisy", "metric": "cpu", "operator": ">", "threshold": -1,
              "cooldown_minutes": 60},
    )
    with Session(engine) as session:
        session.add(MonitorSample(cpu=50.0))
        session.commit()

    assert client.post("/api/notify/evaluate").json()["fired"] == 1
    assert client.post("/api/notify/evaluate").json()["fired"] == 0


def test_a_disabled_rule_never_fires(client):
    rule = client.post(
        "/api/notify/rules",
        json={"name": "off", "metric": "cpu", "operator": ">", "threshold": -1},
    ).json()
    client.patch(f"/api/notify/rules/{rule['id']}", json={"enabled": False})

    with Session(engine) as session:
        session.add(MonitorSample(cpu=99.0))
        session.commit()
    assert client.post("/api/notify/evaluate").json()["fired"] == 0


def test_service_down_rule_reads_the_service_list(client):
    client.post(
        "/api/notify/rules",
        json={"name": "nginx down", "metric": "service_down", "operator": ">",
              "threshold": 0.5, "target": "definitely-not-a-service"},
    )
    fired = client.post("/api/notify/evaluate").json()
    assert fired["fired"] == 1
    assert "definitely-not-a-service" in fired["events"][0]["body"]


def test_delivery_is_skipped_in_dry_run(client):
    channel = client.post(
        "/api/notify/channels",
        json={"name": "hook", "kind": "webhook", "config": {"url": "http://127.0.0.1:9/none"}},
    ).json()
    result = client.post(f"/api/notify/channels/{channel['id']}/test").json()
    assert result["ok"] is True
    assert "dry-run" in result["detail"]


def test_metrics_are_listed_for_the_ui(client):
    keys = {row["key"] for row in client.get("/api/notify/metrics").json()}
    assert {"cpu", "memory", "disk", "cert_expiry", "service_down"} <= keys
