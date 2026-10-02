from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.api import api_router, ws_router
from app.bootstrap import ensure_admin
from app.config import settings
from app.db import engine, init_db
from app.errors import PanelError

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    settings.ensure_dirs()
    app = FastAPI(title="SlimPanel", version="0.1.0", docs_url=f"{settings.entry_path}/api/docs")

    init_db()
    with Session(engine) as session:
        created = ensure_admin(
            session, password=os.environ.get("SLIMPANEL_ADMIN_PASSWORD", "")
        )
    if created:
        print(f"[slimpanel] admin account created: {created[0]} / {created[1]}")

    app.include_router(api_router, prefix=settings.entry_path)
    app.include_router(ws_router, prefix=settings.entry_path)

    app.mount(
        f"{settings.entry_path}/static",
        StaticFiles(directory=STATIC_DIR),
        name="static",
    )

    @app.exception_handler(PanelError)
    async def panel_error_handler(request: Request, exc: PanelError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "info": exc.detail},
        )

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get(f"{settings.entry_path}/")
    def index():
        return RedirectResponse(f"{settings.entry_path}/static/index.html")

    return app


app = create_app()
