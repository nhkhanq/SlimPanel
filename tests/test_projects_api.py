"""Node/Python/Java projects, rendered as systemd units."""
from __future__ import annotations

import pytest

from app.services import projects


@pytest.fixture
def project(client):
    response = client.post(
        "/api/projects",
        json={
            "name": "demo-api",
            "runtime": "node",
            "path": "",
            "command": "node server.js",
            "port": 4000,
            "env": "NODE_ENV=production\nAPI_KEY=abc",
            "autostart": False,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_runtimes_are_reported_with_availability(client):
    rows = client.get("/api/projects/runtimes").json()
    keys = {row["key"] for row in rows}
    assert {"node", "python", "java", "go", "dotnet", "other"} <= keys
    for row in rows:
        assert isinstance(row["available"], bool)


@pytest.mark.parametrize("name", ["A", "x", "has spaces", "sym!bol", "a" * 60, ""])
def test_project_names_are_validated(client, name):
    response = client.post(
        "/api/projects", json={"name": name, "runtime": "node", "command": "node ."}
    )
    assert response.status_code == 400


def test_project_names_are_lowercased(client):
    created = client.post(
        "/api/projects", json={"name": "MixedCase", "runtime": "other", "command": "/bin/true"}
    )
    assert created.status_code == 200
    assert created.json()["name"] == "mixedcase"


def test_unknown_runtime_is_refused(client):
    response = client.post(
        "/api/projects", json={"name": "bad-rt", "runtime": "cobol", "command": "x"}
    )
    assert response.status_code == 400


def test_duplicate_project_name_is_refused(client, project):
    response = client.post(
        "/api/projects", json={"name": "demo-api", "runtime": "node", "command": "node ."}
    )
    assert response.status_code == 409


def test_a_missing_command_is_refused(client):
    response = client.post(
        "/api/projects", json={"name": "nocmd", "runtime": "other", "command": ""}
    )
    assert response.status_code == 400


def test_a_multiline_command_is_refused(client):
    response = client.post(
        "/api/projects", json={"name": "multi", "runtime": "other", "command": "a\nb"}
    )
    assert response.status_code == 400


def test_port_range_is_checked(client):
    response = client.post(
        "/api/projects", json={"name": "badport", "runtime": "node", "command": "node .", "port": 99999}
    )
    assert response.status_code == 400


def test_the_unit_carries_the_environment_and_port(client, project):
    unit = client.get(f"/api/projects/{project['id']}/unit").json()
    body = unit["content"]

    assert "Description=SlimPanel project demo-api" in body
    assert 'Environment="NODE_ENV=production"' in body
    assert 'Environment="API_KEY=abc"' in body
    assert 'Environment="PORT=4000"' in body
    assert "Restart=always" in body
    assert f"WorkingDirectory={project['path']}" in body
    assert unit["path"].endswith("slimpanel-demo-api.service")


def test_an_explicit_port_variable_wins_over_the_field(client):
    created = client.post(
        "/api/projects",
        json={"name": "own-port", "runtime": "other", "command": "/bin/true", "port": 4000,
              "env": "PORT=9999"},
    ).json()
    body = client.get(f"/api/projects/{created['id']}/unit").json()["content"]
    assert 'Environment="PORT=9999"' in body
    assert 'Environment="PORT=4000"' not in body


def test_bad_environment_lines_are_refused(client):
    response = client.post(
        "/api/projects",
        json={"name": "badenv", "runtime": "other", "command": "/bin/true", "env": "not an assignment"},
    )
    assert response.status_code == 400


def test_environment_comments_are_skipped(client):
    created = client.post(
        "/api/projects",
        json={"name": "commented", "runtime": "other", "command": "/bin/true",
              "env": "# a note\nKEY=value\n\n"},
    )
    assert created.status_code == 200
    body = client.get(f"/api/projects/{created.json()['id']}/unit").json()["content"]
    assert 'Environment="KEY=value"' in body
    assert "# a note" not in body


def test_a_relative_command_is_resolved_or_wrapped(client):
    created = client.post(
        "/api/projects", json={"name": "wrapped", "runtime": "other", "command": "my-made-up-binary --go"}
    ).json()
    body = client.get(f"/api/projects/{created['id']}/unit").json()["content"]
    # systemd needs an absolute ExecStart, so an unresolvable name gets a shell.
    assert "ExecStart=/bin/bash -lc" in body


def test_an_absolute_command_is_used_as_is(client):
    created = client.post(
        "/api/projects", json={"name": "absolute", "runtime": "other", "command": "/usr/bin/env FOO=1"}
    ).json()
    body = client.get(f"/api/projects/{created['id']}/unit").json()["content"]
    assert "ExecStart=/usr/bin/env FOO=1" in body


def test_updating_a_project_rewrites_its_unit(client, project):
    client.patch(f"/api/projects/{project['id']}", json={"port": 5555, "command": "node other.js"})
    body = client.get(f"/api/projects/{project['id']}/unit").json()["content"]
    assert 'Environment="PORT=5555"' in body
    assert "other.js" in body


def test_lifecycle_actions_are_restricted(client, project):
    assert client.post(f"/api/projects/{project['id']}/explode").status_code == 400
    for action in ("start", "stop", "restart", "reload"):
        assert client.post(f"/api/projects/{project['id']}/{action}").status_code == 200


def test_autostart_can_be_flipped(client, project):
    body = client.post(f"/api/projects/{project['id']}/autostart/true").json()
    assert body["autostart"] is True


def test_logs_endpoint_answers_even_with_no_output(client, project):
    body = client.get(f"/api/projects/{project['id']}/logs").json()
    assert "lines" in body
    assert body["path"].endswith("demo-api.log")


def test_deleting_a_project_leaves_its_files(client, project, www_root):
    path = project["path"]
    assert client.delete(f"/api/projects/{project['id']}").status_code == 200
    assert client.get(f"/api/projects/{project['id']}").status_code == 404

    from pathlib import Path

    assert Path(path).is_dir()


def test_a_project_root_outside_the_managed_roots_is_refused(client):
    response = client.post(
        "/api/projects", json={"name": "escapee", "runtime": "other", "command": "/bin/true",
                               "path": "/etc/cron.d"}
    )
    assert response.status_code == 403


def test_describe_includes_runtime_state(client, project):
    rows = client.get("/api/projects").json()
    assert rows[0]["unit"] == "slimpanel-demo-api.service"
    assert "state" in rows[0]
    assert rows[0]["url"] == "http://127.0.0.1:4000"
