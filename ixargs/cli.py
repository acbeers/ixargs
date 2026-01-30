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


def _find_command_start(argv: list[str]) -> int:
    """Return index of the command (first non-option) in argv.

    Only ixargs options (-z, -v, -t, -I) are consumed. Everything else,
    including -type, -exec, etc., belongs to the command. This prevents
    argparse from mis-parsing e.g. -type as -t.
    """
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--":
            return i + 1  # command starts after --
        if arg in ("-z", "-v", "-t"):
            i += 1
            continue
        if arg == "-I":
            i += 2
            if i > len(argv):
                return len(argv)  # -I at end, no command
            continue
        # Not an ixargs option - this is the command
        return i
    return len(argv)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = argv if argv is not None else sys.argv[1:]

    # Support -- to explicitly separate ixargs options from the command
    if "--" in argv:
        sep_idx = argv.index("--")
        options_part = argv[:sep_idx]
        command_part = argv[sep_idx + 1:]
    else:
        cmd_start = _find_command_start(argv)
        options_part = argv[:cmd_start]
        command_part = argv[cmd_start:]

    parser = argparse.ArgumentParser(
        prog="ixargs",
        description="Run commands against stdin lines in a split-pane TUI.",
        epilog="Example: some_tool | ixargs -z cat. Use -- to separate ixargs options from command args that look like options (e.g. find -exec).",
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

    parsed, _ = parser.parse_known_args(options_part)
    parsed.cmd = command_part[0] if command_part else ""
    parsed.args = list(command_part[1:]) if len(command_part) > 1 else []

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
