from __future__ import annotations

import asyncio
import fcntl
import os
import pty
import signal
import struct
import termios

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.security import read_session_token

router = APIRouter(tags=["terminal"])

SHELL = os.environ.get("SLIMPANEL_SHELL", "/bin/bash")
READ_SIZE = 4096


def _resize(fd: int, rows: int, cols: int) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


@router.websocket("/ws/terminal")
async def terminal(websocket: WebSocket):
    token = websocket.cookies.get("slimpanel_session", "")
    if not read_session_token(token):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(SHELL, [SHELL, "-l"])

    loop = asyncio.get_running_loop()
    _resize(fd, 24, 80)

    async def pump_out() -> None:
        while True:
            try:
                data = await loop.run_in_executor(None, os.read, fd, READ_SIZE)
            except OSError:
                break
            if not data:
                break
            await websocket.send_text(data.decode("utf-8", errors="replace"))

    reader = asyncio.create_task(pump_out())
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "resize":
                _resize(fd, int(message.get("rows", 24)), int(message.get("cols", 80)))
            elif message.get("type") == "input":
                os.write(fd, message.get("data", "").encode())
    except (WebSocketDisconnect, ValueError, RuntimeError):
        pass
    finally:
        reader.cancel()
        os.close(fd)
        try:
            os.kill(pid, signal.SIGHUP)
            os.waitpid(pid, os.WNOHANG)
        except (ProcessLookupError, ChildProcessError):
            pass
