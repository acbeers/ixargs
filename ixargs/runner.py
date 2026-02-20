"""Run a command and capture stdout+stderr, with ANSI color when using a PTY."""

from __future__ import annotations

import codecs
import errno
import fcntl
import os
import pty
import select
import struct
import subprocess
import termios
import threading
import tty
from collections.abc import Callable


def _set_pty_winsize(slave_fd: int, width: int, height: int) -> None:
    """Set the PTY window size so child processes (e.g. delta) see correct dimensions."""
    if width <= 0 or height <= 0:
        return
    try:
        tiocswinsz = getattr(termios, "TIOCSWINSZ", None)
        if tiocswinsz is None:
            return
        # winsize: (ws_row, ws_col, ws_xpixel, ws_ypixel)
        buf = struct.pack("HHHH", height, width, 0, 0)
        fcntl.ioctl(slave_fd, tiocswinsz, buf)
    except (OSError, struct.error):
        pass


def _run_capture_pty(cmd: list[str], env: dict[str, str]) -> str:
    """Capture via PTY so the child sees a TTY and emits color. Returns decoded str."""
    master_fd, slave_fd = pty.openpty()
    try:
        try:
            tty.setraw(slave_fd, termios.TCSANOW)
        except (termios.error, OSError):
            pass

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
        os.set_blocking(master_fd, False)
        try:
            while True:
                r, _, _ = select.select([master_fd], [], [], 0.1)
                if r:
                    try:
                        data = os.read(master_fd, 65536)
                    except OSError as e:
                        if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                            break
                        data = None
                    if data is not None:
                        if not data:
                            break
                        chunks.append(data)
                if proc.poll() is not None:
                    while True:
                        try:
                            data = os.read(master_fd, 65536)
                        except OSError as e:
                            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                                break
                            break
                        if not data:
                            break
                        chunks.append(data)
                    break
        finally:
            try:
                os.set_blocking(master_fd, True)
            except OSError:
                pass
        proc.wait()
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


def _run_capture_pipe(cmd: list[str], env: dict[str, str]) -> str:
    """Capture via PIPE (no color). Returns decoded str."""
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


def _effective_git_pager(env: dict[str, str]) -> str | None:
    """Return the git pager command if it is delta (so we can use it with DELTA_PAGER=cat)."""
    pager = env.get("GIT_PAGER", "").strip()
    if not pager:
        try:
            r = subprocess.run(
                ["git", "config", "--get", "core.pager"],
                capture_output=True,
                text=True,
                timeout=2,
                env=env,
            )
            if r.returncode == 0 and r.stdout:
                pager = r.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    if pager and "delta" in pager.lower():
        return pager
    return None


def _apply_pager_env(env: dict[str, str]) -> None:
    """Set PAGER/GIT_PAGER so output is non-interactive; use delta with DELTA_PAGER=cat when configured."""
    git_pager = _effective_git_pager(env)
    if git_pager is not None:
        env["GIT_PAGER"] = git_pager
        env["DELTA_PAGER"] = "cat"
    else:
        env["GIT_PAGER"] = "cat"
    env["PAGER"] = "cat"


def run_capture(cmd: list[str], env: dict[str, str] | None = None) -> str:
    """Run command, capture stdout+stderr. Uses PTY for color when possible."""
    env = dict(env) if env is not None else dict(os.environ)
    env.setdefault("TERM", "xterm-256color")
    _apply_pager_env(env)
    try:
        return _run_capture_pty(cmd, env)
    except (OSError, FileNotFoundError):
        return _run_capture_pipe(cmd, env)


def _read_and_stream(
    read_fn: Callable[[int], bytes], on_chunk: Callable[[str], None]
) -> None:
    """Read from read_fn in a loop, decode incrementally, call on_chunk for each piece."""
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    while True:
        data = read_fn(65536)
        if not data:
            break
        s = decoder.decode(data, final=False)
        if s:
            on_chunk(s)
    s = decoder.decode(b"", final=True)
    if s:
        on_chunk(s)


def _run_streaming_pty(
    cmd: list[str],
    env: dict[str, str],
    on_chunk: Callable[[str], None],
    cancel_event: threading.Event | None = None,
    *,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Stream command output via PTY. Calls on_chunk for each decoded piece."""
    master_fd, slave_fd = pty.openpty()
    try:
        try:
            tty.setraw(slave_fd, termios.TCSANOW)
        except (termios.error, OSError):
            pass
        if width is not None and height is not None:
            _set_pty_winsize(slave_fd, width, height)

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

    try:
        os.set_blocking(master_fd, False)
        try:
            decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    try:
                        proc.kill()
                    except OSError:
                        pass
                    break
                r, _, _ = select.select([master_fd], [], [], 0.1)
                if r:
                    try:
                        data = os.read(master_fd, 65536)
                    except OSError as e:
                        if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                            break
                        data = None
                    if data is not None:
                        if not data:
                            break
                        s = decoder.decode(data, final=False)
                        if s:
                            on_chunk(s)
                if proc.poll() is not None:
                    while True:
                        try:
                            data = os.read(master_fd, 65536)
                        except OSError as e:
                            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                                break
                            break
                        if not data:
                            break
                        s = decoder.decode(data, final=False)
                        if s:
                            on_chunk(s)
                    s = decoder.decode(b"", final=True)
                    if s:
                        on_chunk(s)
                    break
        finally:
            try:
                os.set_blocking(master_fd, True)
            except OSError:
                pass
        proc.wait()
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


def _run_streaming_pipe(
    cmd: list[str],
    env: dict[str, str],
    on_chunk: Callable[[str], None],
    cancel_event: threading.Event | None = None,
) -> None:
    """Stream command output via PIPE. Calls on_chunk for each decoded piece."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        env=env,
        start_new_session=True,
    )
    assert proc.stdout is not None

    def kill_on_cancel() -> None:
        cancel_event.wait()
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass

    if cancel_event is not None:
        threading.Thread(target=kill_on_cancel, daemon=True).start()

    def read_stdout(n: int) -> bytes:
        data = proc.stdout.read(n)
        return data if data is not None else b""

    try:
        _read_and_stream(read_stdout, on_chunk)
    finally:
        try:
            if proc.poll() is None:
                proc.kill()
        except OSError:
            pass
        proc.wait()


def run_capture_streaming(
    cmd: list[str],
    on_chunk: Callable[[str], None],
    env: dict[str, str] | None = None,
    cancel_event: threading.Event | None = None,
    *,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Run command and stream stdout+stderr by calling on_chunk for each piece."""
    env = dict(env) if env is not None else dict(os.environ)
    env.setdefault("TERM", "xterm-256color")
    _apply_pager_env(env)
    if width is not None and width > 0 and height is not None and height > 0:
        env["COLUMNS"] = str(width)
        env["LINES"] = str(height)
    try:
        _run_streaming_pty(
            cmd, env, on_chunk, cancel_event, width=width, height=height
        )
    except (OSError, FileNotFoundError):
        _run_streaming_pipe(cmd, env, on_chunk, cancel_event)
