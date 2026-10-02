from fastapi import APIRouter

from app.api import (
    apikeys,
    apps,
    auth,
    backup,
    cron,
    databases,
    docker,
    files,
    ftp,
    importer,
    logs,
    monitor,
    notify,
    oneclick,
    php,
    projects,
    recycle,
    security,
    settings_api,
    sites,
    ssl,
    system,
    tasks,
    terminal,
    toolbox,
)

api_router = APIRouter(prefix="/api")

for module in (
    auth,
    sites,
    ssl,
    databases,
    files,
    recycle,
    system,
    monitor,
    php,
    apps,
    projects,
    docker,
    ftp,
    security,
    toolbox,
    cron,
    backup,
    notify,
    logs,
    tasks,
    apikeys,
    oneclick,
    settings_api,
    importer,
):
    api_router.include_router(module.router)

ws_router = terminal.router
