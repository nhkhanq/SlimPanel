from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass

from app.config import settings
from app.errors import CommandFailed


@dataclass
class Result:
    code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.code == 0

    @property
    def output(self) -> str:
        return (self.stdout + "\n" + self.stderr).strip()


def run(
    command: str | list[str],
    timeout: int = 60,
    check: bool = False,
    stdin: str | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> Result:
    argv = shlex.split(command) if isinstance(command, str) else list(command)

    if settings.dry_run:
        return Result(0, f"dry-run: {' '.join(argv)}", "")

    try:
        proc = subprocess.run(
            argv,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
    except FileNotFoundError:
        result = Result(127, "", f"command not found: {argv[0]}")
    except subprocess.TimeoutExpired:
        result = Result(124, "", f"timeout after {timeout}s: {' '.join(argv)}")
    else:
        result = Result(proc.returncode, proc.stdout or "", proc.stderr or "")

    if check and not result.ok:
        raise CommandFailed(f"Command failed: {argv[0]}", result.output)
    return result
