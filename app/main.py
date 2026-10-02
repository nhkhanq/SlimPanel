from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.api import api_router, ws_router
from app.bootstrap import ensure_admin
from app.config import settings
from app.db import engine, init_db
from app.errors import PanelError

DIST_DIR = Path(__file__).resolve().parent / "static" / "dist"

BUILD_HINT = """<!doctype html>
<html><head><meta charset="utf-8"><title>SlimPanel</title></head>
<body style="font-family:system-ui;max-width:40rem;margin:4rem auto;line-height:1.6">
<h1>The web interface is not built</h1>
<p>Run this once, then reload:</p>
<pre style="background:#f4f4f4;padding:12px;border-radius:8px">cd web &amp;&amp; npm install &amp;&amp; npm run build</pre>
<p>The API is already running at <code>/api/docs</code>.</p>
</body></html>
"""


def create_app() -> FastAPI:
    settings.ensure_dirs()
    app = FastAPI(title="SlimPanel", version="0.2.0", docs_url=f"{settings.entry_path}/api/docs")

    init_db()
    with Session(engine) as session:
        created = ensure_admin(session, password=os.environ.get("SLIMPANEL_ADMIN_PASSWORD", ""))
    if created:
        print(f"[slimpanel] admin account created: {created[0]} / {created[1]}")

    @app.exception_handler(PanelError)
    async def panel_error_handler(request: Request, exc: PanelError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "info": exc.detail},
        )

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    app.include_router(api_router, prefix=settings.entry_path)
    app.include_router(ws_router, prefix=settings.entry_path)

    if DIST_DIR.is_dir():
        app.mount(
            f"{settings.entry_path}/",
            StaticFiles(directory=DIST_DIR, html=True),
            name="ui",
        )
    else:

        @app.get(f"{settings.entry_path}/", response_class=HTMLResponse)
        def build_hint():
            return BUILD_HINT

    return app


app = create_app()
