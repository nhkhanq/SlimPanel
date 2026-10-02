from app.security import totp_code

from tests.conftest import ADMIN_PASSWORD


def test_login_rejects_bad_password(anon):
    response = anon.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert response.status_code == 401


def test_protected_route_requires_session(anon):
    assert anon.get("/api/sites").status_code == 401


def test_login_then_me(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_logout_clears_session(client):
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_change_password_requires_old_password(client):
    bad = client.post(
        "/api/auth/password", json={"old_password": "wrong", "new_password": "newpassword1"}
    )
    assert bad.status_code == 400

    good = client.post(
        "/api/auth/password",
        json={"old_password": ADMIN_PASSWORD, "new_password": "newpassword1"},
    )
    assert good.status_code == 200


def test_totp_enable_flow(client):
    secret = client.post("/api/auth/totp/setup").json()["secret"]
    assert client.post("/api/auth/totp/enable", json={"code": "000000"}).status_code == 400

    enabled = client.post("/api/auth/totp/enable", json={"code": totp_code(secret)})
    assert enabled.status_code == 200
    assert client.get("/api/auth/me").json()["totp_enabled"] is True

    client.post("/api/auth/logout")
    without_code = client.post(
        "/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD}
    )
    assert without_code.status_code == 401

    with_code = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD, "code": totp_code(secret)},
    )
    assert with_code.status_code == 200


def test_login_logs_record_attempts(client):
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "admin", "password": "bad"})
    client.post("/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD})

    logs = client.get("/api/auth/login-logs").json()
    assert any(entry["success"] is False for entry in logs)
    assert any(entry["success"] is True for entry in logs)
