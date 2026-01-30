"""Run a command and capture stdout+stderr."""

from __future__ import annotations

import os
import subprocess


def run_capture(cmd: list[str], env: dict[str, str] | None = None) -> str:
    """Run command, capture stdout+stderr. Returns decoded str."""
    env = dict(env) if env is not None else dict(os.environ)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        env=env,
        start_new_session=True,
    )
    assert proc.stdout is not None
    out, _ = proc.communicate()
    return out.decode("utf-8", errors="replace")
