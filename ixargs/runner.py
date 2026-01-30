"""Run a command in a PTY and capture output with ANSI colors preserved."""

from __future__ import annotations

import os
import pty
import subprocess


def run_capture(cmd: list[str], env: dict[str, str] | None = None) -> str:
    """Run command in a PTY, capture stdout+stderr with ANSI preserved. Returns decoded str."""
    env = dict(env) if env is not None else dict(os.environ)
    env.setdefault("TERM", "xterm-256color")

    master_fd, slave_fd = pty.openpty()
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=slave_fd,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )
    except Exception:
        os.close(slave_fd)
        os.close(master_fd)
        raise
    os.close(slave_fd)

    chunks: list[bytes] = []
    try:
        while True:
            try:
                data = os.read(master_fd, 65536)
            except OSError:
                break
            if not data:
                break
            chunks.append(data)
        proc.wait()
        # Drain any remaining output after process exits
        while True:
            try:
                data = os.read(master_fd, 65536)
            except OSError:
                break
            if not data:
                break
            chunks.append(data)
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass
        try:
            proc.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    return b"".join(chunks).decode("utf-8", errors="replace")
