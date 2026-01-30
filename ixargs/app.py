"""ixargs TUI application."""

from __future__ import annotations

import asyncio
import os
import sys
import threading
import time
from typing import Callable

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Markdown, Static

from ixargs.runner import run_capture_streaming


HELP_MARKDOWN = """
# ixargs shortcuts

**Input list** (focus on left/top panel):
| Key | Action |
|-----|--------|
| `j` / `k` / `↑` / `↓` | Next / previous line |

**Output panel** (scroll output from anywhere):
| Key | Action |
|-----|--------|
| ` ` (space) | Next page |
| `b` | Previous page |
| `<` | Top of output |
| `>` | Bottom of output |

**Global:**
| Key | Action |
|-----|--------|
| `q` | Quit |
| `?` | This help |
| `/` | Search |
| `n` / `N` | Search next / previous |
"""


class HelpScreen(Screen[None]):
    """Help overlay for keyboard shortcuts."""

    BINDINGS = [("q", "close", "Close"), ("escape", "close", "Close")]

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Markdown(HELP_MARKDOWN))

    def action_close(self) -> None:
        self.app.pop_screen()


def make_list_content(lines: list[str], index: int, width: int) -> Text:
    t = Text()
    for i, line in enumerate(lines):
        row = (f"{i + 1:4} " + line)[: width - 1] + "\n"
        if i == index:
            t.append(row, style="reverse")
        else:
            t.append(row)
    return t


class ListScrollContainer(VerticalScroll):
    """VerticalScroll that handles j/k/up/down for line selection (input list)."""

    BINDINGS = [
        Binding("j", "line_down", "Down", show=False),
        Binding("k", "line_up", "Up", show=False),
        Binding("down", "line_down", "Down", show=False),
        Binding("up", "line_up", "Up", show=False),
    ]

    def action_line_down(self) -> None:
        self.app.action_line_down()

    def action_line_up(self) -> None:
        self.app.action_line_up()


class ListPanel(Static):
    """Left/top panel showing stdin lines."""

    def __init__(
        self,
        lines: list[str],
        index: int = 0,
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, markup=False)
        self.lines = lines
        self.index = index

    def render(self) -> Text:
        w = self.size.width if self.size else 80
        return make_list_content(self.lines, self.index, max(20, w))

    def set_index(self, index: int) -> None:
        self.index = max(0, min(len(self.lines) - 1, index))
        self.refresh()


class OutputScrollContainer(VerticalScroll):
    """VerticalScroll that handles space/b/</> for output panel scrolling."""

    BINDINGS = [
        Binding("space", "page_down", "Page down", show=False),
        Binding("b", "page_up", "Page up", show=False),
        Binding("<", "scroll_home", "Top", show=False),
        Binding(">", "scroll_end", "Bottom", show=False),
    ]

    def _mark_scrolling(self) -> None:
        """Notify app that user is scrolling."""
        if hasattr(self.app, "_mark_user_scrolling"):
            self.app._mark_user_scrolling()

    def action_page_down(self) -> None:
        self._mark_scrolling()
        self.scroll_page_down(animate=False)

    def action_page_up(self) -> None:
        self._mark_scrolling()
        self.scroll_page_up(animate=False)

    def action_scroll_home(self) -> None:
        self._mark_scrolling()
        self.scroll_home(animate=False, immediate=True)

    def action_scroll_end(self) -> None:
        self._mark_scrolling()
        self.scroll_end(animate=False, immediate=True)

    def action_scroll_down(self) -> None:
        """Override default scroll_down to mark scrolling."""
        self._mark_scrolling()
        super().action_scroll_down()

    def action_scroll_up(self) -> None:
        """Override default scroll_up to mark scrolling."""
        self._mark_scrolling()
        super().action_scroll_up()


class OutputPanel(Static):
    """Right/bottom panel showing command output."""

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__("", name=name, id=id, markup=False)

    def set_output(self, text: str) -> None:
        try:
            self.update(Text.from_ansi(text or "(no output)"))
        except Exception:
            self.update(text or "(no output)")


def _css_path() -> str:
    """Resolve CSS path for development vs PyInstaller frozen bundle."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "ixargs", "app.css")
    return "app.css"


class IxargsApp(App[None]):
    """Main ixargs TUI."""

    TITLE = "ixargs"
    CSS_PATH = _css_path()
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
        Binding("space", "output_page_down", "Output page down", show=False),
        Binding("b", "output_page_up", "Output page up", show=False),
        Binding("<", "output_top", "Output top", show=False),
        Binding(">", "output_bottom", "Output bottom", show=False),
        Binding("/", "search", "Search", show=False),
        Binding("n", "search_next", "Next", show=False),
        Binding("N", "search_prev", "Prev", show=False),
    ]

    def __init__(
        self,
        lines: list[str],
        cmd_for_line: Callable[[str], list[str]],
        *,
        horizontal: bool = True,
        list_size: None | int | str = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.lines = lines
        self.cmd_for_line = cmd_for_line
        self.horizontal = horizontal
        self.list_size = list_size
        self._run_id = 0
        self._cancel_run = threading.Event()
        self._search_query: str | None = None
        self._search_matches: list[int] = []
        self._search_index = 0
        self._user_scrolling = False
        self._last_scroll_time = 0.0

    def compose(self) -> ComposeResult:
        root: Horizontal | Vertical
        if self.horizontal:
            root = Horizontal(
                ListScrollContainer(
                    ListPanel(self.lines, 0, id="list-panel"),
                    id="list-scroll",
                ),
                OutputScrollContainer(
                    OutputPanel(id="output-panel"),
                    id="output-scroll",
                ),
                id="root",
                classes="horizontal",
            )
        else:
            root = Vertical(
                ListScrollContainer(
                    ListPanel(self.lines, 0, id="list-panel"),
                    id="list-scroll",
                ),
                OutputScrollContainer(
                    OutputPanel(id="output-panel"),
                    id="output-scroll",
                ),
                id="root",
                classes="vertical",
            )
        yield root
        yield Footer()

    def on_mount(self) -> None:
        list_scroll = self.query_one("#list-scroll", ListScrollContainer)
        self.set_focus(list_scroll)
        if self.horizontal:
            if self.list_size is None:
                # Auto fit: size list panel to content width (line numbers + longest line), capped by CSS max-width 50%
                content_width = 20  # minimum for "   1 " + short line
                for line in self.lines:
                    content_width = max(content_width, 5 + len(line))
                list_scroll.styles.min_width = content_width
            elif isinstance(self.list_size, int):
                list_scroll.styles.width = self.list_size
            else:
                list_scroll.styles.width = self.list_size  # e.g. "25%"
        else:
            if isinstance(self.list_size, int):
                list_scroll.styles.height = self.list_size
            else:
                list_scroll.styles.height = self.list_size  # e.g. "25%"
        self.run_cmd_for_index(0)

    async def _run_capture_and_show(self, cmd: list[str], rid: int, idx: int) -> None:
        """Run command in thread pool, streaming output to the UI as it arrives."""
        loop = asyncio.get_running_loop()
        cmd_line = " $ " + " ".join(cmd) + "\n\n"
        chunks: list[str] = [cmd_line]
        last_update: list[float] = [0.0]
        throttle_sec = 0.15  # Increased from 0.05 to reduce update frequency
        skipped_updates: list[int] = [0]

        def schedule_update(force: bool = False) -> None:
            # Skip update if user is actively scrolling (unless forced final update)
            if not force and self._user_scrolling:
                skipped_updates[0] += 1
                return
            
            full = "".join(chunks)
            try:
                loop.call_soon_threadsafe(
                    lambda: self._set_output_if_current(full, rid, idx)
                )
                skipped_updates[0] = 0
            except RuntimeError:
                pass  # Loop may be closed during shutdown

        def on_chunk(s: str) -> None:
            chunks.append(s)
            now = time.monotonic()
            # More aggressive throttling: increase interval if updates are being skipped
            effective_throttle = throttle_sec * (1 + min(skipped_updates[0] * 0.5, 3))
            if now - last_update[0] >= effective_throttle:
                last_update[0] = now
                schedule_update()

        def run_streaming() -> None:
            try:
                run_capture_streaming(cmd, on_chunk, cancel_event=self._cancel_run)
            except Exception as e:
                chunks.append(f"(error)\n{e!s}")
            schedule_update(force=True)  # Final update (catches throttled tail + errors)

        await asyncio.to_thread(run_streaming)

    def run_cmd_for_index(self, index: int) -> None:
        line = self.lines[index]
        cmd = self.cmd_for_line(line)
        out_panel = self.query_one("#output-panel", OutputPanel)
        out_panel.set_output(" $ " + " ".join(cmd) + "\n\nRunning...")
        self._cancel_run.clear()
        self._run_id += 1
        rid = self._run_id
        self.run_worker(
            self._run_capture_and_show(cmd, rid, index),
            exclusive=False,
            group="run",
        )

    def _set_output_if_current(self, text: str, rid: int, idx: int | None) -> None:
        """Update output panel only if this run is still current."""
        if rid != self._run_id:
            return
        try:
            self._set_output(text, idx)
        except Exception:
            pass  # App may be shutting down; ignore widget update errors

    def _set_output(self, text: str, idx: int | None) -> None:
        out_panel = self.query_one("#output-panel", OutputPanel)
        out_panel.set_output(text)
        if idx is not None:
            list_panel = self.query_one("#list-panel", ListPanel)
            if list_panel.index == idx:
                self._search_matches = []
                self._search_query = None

    def action_quit(self) -> None:
        self._cancel_run.set()  # Signal runner to kill subprocess for fast exit
        self.exit()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_line_down(self) -> None:
        lp = self.query_one("#list-panel", ListPanel)
        if lp.index >= len(self.lines) - 1:
            return
        n = lp.index + 1
        lp.set_index(n)
        self._scroll_list_to(n)
        self.run_cmd_for_index(n)

    def action_line_up(self) -> None:
        lp = self.query_one("#list-panel", ListPanel)
        if lp.index <= 0:
            return
        n = lp.index - 1
        lp.set_index(n)
        self._scroll_list_to(n)
        self.run_cmd_for_index(n)

    def _scroll_list_to(self, index: int) -> None:
        try:
            scroll = self.query_one("#list-scroll", ListScrollContainer)
            scroll.scroll_to(y=index, animate=False)
        except Exception:
            pass

    def _mark_user_scrolling(self) -> None:
        """Mark that user is actively scrolling; pause output updates briefly."""
        self._user_scrolling = True
        self._last_scroll_time = time.monotonic()
        # Schedule a check to clear the flag after user stops scrolling
        self.set_timer(0.3, self._check_scroll_idle)

    def _check_scroll_idle(self) -> None:
        """Clear scrolling flag if user hasn't scrolled recently."""
        if time.monotonic() - self._last_scroll_time >= 0.25:
            self._user_scrolling = False

    def action_output_page_down(self) -> None:
        self._mark_user_scrolling()
        try:
            self.query_one("#output-scroll", OutputScrollContainer).scroll_page_down(
                animate=False
            )
        except Exception:
            pass

    def action_output_page_up(self) -> None:
        self._mark_user_scrolling()
        try:
            self.query_one("#output-scroll", OutputScrollContainer).scroll_page_up(
                animate=False
            )
        except Exception:
            pass

    def action_output_top(self) -> None:
        self._mark_user_scrolling()
        try:
            self.query_one("#output-scroll", OutputScrollContainer).scroll_home(
                animate=False, immediate=True
            )
        except Exception:
            pass

    def action_output_bottom(self) -> None:
        self._mark_user_scrolling()
        try:
            self.query_one("#output-scroll", OutputScrollContainer).scroll_end(
                animate=False, immediate=True
            )
        except Exception:
            pass

    def action_search(self) -> None:
        self._search_query = ""
        self._search_matches = []
        self._search_index = 0
        self.notify("Search: type in next version. Use n/N for next/prev.", timeout=3)

    def action_search_next(self) -> None:
        if not self._search_matches:
            return
        self._search_index = (self._search_index + 1) % len(self._search_matches)
        self._scroll_output_to_match()

    def action_search_prev(self) -> None:
        if not self._search_matches:
            return
        self._search_index = (self._search_index - 1) % len(self._search_matches)
        self._scroll_output_to_match()

    def _scroll_output_to_match(self) -> None:
        pass  # TODO: scroll output to self._search_matches[self._search_index]
