"""Command-line interface for ixargs."""

from __future__ import annotations

import argparse
import os
import sys

from ixargs.app import IxargsApp


def _reconnect_stdin_to_tty() -> None:
    """Reconnect stdin to the controlling TTY so the TUI can read keyboard input.

    Textual reads key events from sys.__stdin__. When ixargs is run as
    `... | ixargs cmd`, stdin is the pipe; we consume it for input lines.
    The TUI must read keys from the terminal, so we dup /dev/tty onto fd 0.
    """
    try:
        tty_fd = os.open("/dev/tty", os.O_RDONLY)
    except OSError as e:
        sys.exit(f"ixargs: no controlling terminal (/dev/tty): {e}")
    try:
        os.dup2(tty_fd, 0)
    finally:
        os.close(tty_fd)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ixargs",
        description="Run commands against stdin lines in a split-pane TUI.",
        epilog="Example: some_tool | ixargs -z cat",
    )
    parser.add_argument(
        "-z",
        action="store_true",
        default=True,
        dest="horizontal",
        help="Split horizontally (list on left). Default.",
    )
    parser.add_argument(
        "-v",
        action="store_true",
        dest="vertical",
        help="Split vertically (list on top).",
    )
    parser.add_argument(
        "-t",
        action="store_true",
        dest="trim",
        help="Trim leading and trailing whitespace from each input line.",
    )
    parser.add_argument(
        "-I",
        dest="replstr",
        metavar="replstr",
        default=None,
        help="Replace replstr in args with each stdin line instead of appending it.",
    )
    parser.add_argument(
        "cmd",
        help="Command to run for each line.",
    )
    parser.add_argument(
        "args",
        nargs="*",
        metavar="arg",
        help="Arguments to pass to the command.",
    )
    parsed = parser.parse_args(argv)
    if parsed.vertical:
        parsed.horizontal = False
    return parsed


def read_stdin_lines(trim: bool = False) -> list[str]:
    """Read and return non-empty lines from stdin.

    If trim is True, strip leading and trailing whitespace from each line.
    """
    lines = [line.rstrip("\n") for line in sys.stdin.readlines()]
    if trim:
        lines = [line.strip() for line in lines]
    return [line for line in lines if (line if trim else line.strip())]


def build_cmd(parsed: argparse.Namespace, line: str) -> list[str]:
    """Build command argv for the given stdin line."""
    cmd = parsed.cmd
    args = list(parsed.args)
    if parsed.replstr is not None:
        repl = parsed.replstr
        out: list[str] = [cmd]
        for a in args:
            out.append(a.replace(repl, line) if repl in a else a)
        return out
    return [cmd, *args, line]


def main(argv: list[str] | None = None) -> None:
    parsed = parse_args(argv)
    if not parsed.cmd:
        sys.exit("ixargs: command required. Usage: ... | ixargs [options] cmd [args...]")

    lines = read_stdin_lines(trim=parsed.trim)
    if not lines:
        sys.exit("ixargs: no input lines from stdin.")

    _reconnect_stdin_to_tty()

    def cmd_for_line(line: str) -> list[str]:
        return build_cmd(parsed, line)

    app = IxargsApp(
        lines=lines,
        cmd_for_line=cmd_for_line,
        horizontal=parsed.horizontal,
    )
    app.run()
