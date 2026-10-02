from fastapi import APIRouter

from app.api import auth, backup, cron, databases, files, logs, sites, ssl, system, terminal

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(sites.router)
api_router.include_router(ssl.router)
api_router.include_router(databases.router)
api_router.include_router(files.router)
api_router.include_router(system.router)
api_router.include_router(cron.router)
api_router.include_router(backup.router)
api_router.include_router(logs.router)

ws_router = terminal.router
