from __future__ import annotations

import os

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=os.environ.get("SLIMPANEL_RELOAD", "") == "1",
    )
