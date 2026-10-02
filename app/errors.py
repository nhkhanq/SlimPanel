from __future__ import annotations

from fastapi import HTTPException, status


class PanelError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.message = message
        self.detail = detail


class NotFound(PanelError):
    status_code = status.HTTP_404_NOT_FOUND


class Conflict(PanelError):
    status_code = status.HTTP_409_CONFLICT


class UnsafePath(PanelError):
    status_code = status.HTTP_403_FORBIDDEN


class CommandFailed(PanelError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


def http_error(exc: PanelError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)
