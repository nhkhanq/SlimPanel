from __future__ import annotations

import os
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="slimpanel-test-"))
WWW = TMP / "wwwroot"
LOGS = TMP / "wwwlogs"

for directory in (TMP / "data", WWW, LOGS):
    directory.mkdir(parents=True, exist_ok=True)

os.environ.update(
    {
        "SLIMPANEL_CONFIG": str(TMP / "missing.json"),
        "SLIMPANEL_DATA_DIR": str(TMP / "data"),
        "SLIMPANEL_WWW_ROOT": str(WWW),
        "SLIMPANEL_LOG_ROOT": str(LOGS),
        "SLIMPANEL_FILE_ROOTS": f"{WWW},{LOGS}",
        "SLIMPANEL_CRON_TARGET": str(TMP / "cron.d-slimpanel"),
        "SLIMPANEL_SECRET_KEY": "test-secret-key",
        "SLIMPANEL_ADMIN_PASSWORD": "test-password-123",
        "SLIMPANEL_DRY_RUN": "1",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import SQLModel, Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import engine  # noqa: E402
from app.main import app  # noqa: E402

ADMIN_PASSWORD = "test-password-123"


@pytest.fixture
def tmp_root() -> Path:
    return TMP


@pytest.fixture
def www_root() -> Path:
    return WWW


@pytest.fixture(autouse=True)
def clean_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        from app.bootstrap import ensure_admin

        ensure_admin(session, password=ADMIN_PASSWORD)
    yield
    for stale in settings.vhost_dir.glob("*.conf*"):
        stale.unlink()


@pytest.fixture
def session():
    with Session(engine) as db:
        yield db


@pytest.fixture
def anon() -> TestClient:
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client(anon: TestClient) -> TestClient:
    response = anon.post(
        "/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return anon
