"""ixargs TUI application."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Callable

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Markdown, Static

from ixargs.runner import run_capture


HELP_MARKDOWN = """
# ixargs shortcuts

| Key | Action |
|-----|--------|
| `j` / `↓` | Next line |
| `k` / `↑` | Previous line |
| ` ` (space) | Next page |
| `b` | Previous page |
| `<` | Top of output |
| `>` | Bottom of output |
| `q` | Quit |
| `?` | This help |
| `/` | Search |
| `n` | Search next |
| `N` | Search previous |
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
    """VerticalScroll that delegates up/down arrow keys to the app for line selection."""

    BINDINGS = [
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
        Binding("j", "line_down", "Down", show=False),
        Binding("k", "line_up", "Up", show=False),
        Binding("down", "line_down", "Down", show=False),
        Binding("up", "line_up", "Up", show=False),
        Binding("space", "page_down", "Page down", show=False),
        Binding("b", "page_up", "Page up", show=False),
        Binding("<", "output_top", "Top", show=False),
        Binding(">", "output_bottom", "Bottom", show=False),
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
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.lines = lines
        self.cmd_for_line = cmd_for_line
        self.horizontal = horizontal
        self._run_id = 0
        self._search_query: str | None = None
        self._search_matches: list[int] = []
        self._search_index = 0

    def compose(self) -> ComposeResult:
        root: Horizontal | Vertical
        if self.horizontal:
            root = Horizontal(
                ListScrollContainer(
                    ListPanel(self.lines, 0, id="list-panel"),
                    id="list-scroll",
                ),
                VerticalScroll(
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
                VerticalScroll(
                    OutputPanel(id="output-panel"),
                    id="output-scroll",
                ),
                id="root",
                classes="vertical",
            )
        yield root
        yield Footer()

    def on_mount(self) -> None:
        if self.horizontal:
            # Size list panel to content width (line numbers + longest line), capped by CSS max-width 50%
            content_width = 20  # minimum for "   1 " + short line
            for line in self.lines:
                content_width = max(content_width, 5 + len(line))
            list_scroll = self.query_one("#list-scroll", VerticalScroll)
            list_scroll.styles.min_width = content_width
        self.run_cmd_for_index(0)

    async def _run_capture_and_show(self, cmd: list[str], rid: int, idx: int) -> None:
        """Run command in thread pool, then update output panel from main loop."""
        try:
            out = await asyncio.to_thread(run_capture, cmd)
        except Exception as e:
            out = f"(error)\n{e!s}"
        if rid != self._run_id:
            return
        cmd_line = " $ " + " ".join(cmd) + "\n\n"
        self._set_output(cmd_line + out, idx)

    def run_cmd_for_index(self, index: int) -> None:
        line = self.lines[index]
        cmd = self.cmd_for_line(line)
        out_panel = self.query_one("#output-panel", OutputPanel)
        out_panel.set_output(" $ " + " ".join(cmd) + "\n\nRunning...")
        self._run_id += 1
        rid = self._run_id
        self.run_worker(
            self._run_capture_and_show(cmd, rid, index),
            exclusive=False,
            group="run",
        )

    def _set_output(self, text: str, idx: int | None) -> None:
        out_panel = self.query_one("#output-panel", OutputPanel)
        out_panel.set_output(text)
        if idx is not None:
            list_panel = self.query_one("#list-panel", ListPanel)
            if list_panel.index == idx:
                self._search_matches = []
                self._search_query = None

    def action_quit(self) -> None:
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
            scroll = self.query_one("#list-scroll", VerticalScroll)
            scroll.scroll_to(y=index, animate=False)
        except Exception:
            pass

    def action_page_down(self) -> None:
        lp = self.query_one("#list-panel", ListPanel)
        try:
            scroll = self.query_one("#list-scroll", VerticalScroll)
            h = scroll.size.height if scroll.size else 20
        except Exception:
            h = 20
        n = min(len(self.lines) - 1, lp.index + max(1, h))
        if n != lp.index:
            lp.set_index(n)
            self._scroll_list_to(n)
            self.run_cmd_for_index(n)

    def action_page_up(self) -> None:
        lp = self.query_one("#list-panel", ListPanel)
        try:
            scroll = self.query_one("#list-scroll", VerticalScroll)
            h = scroll.size.height if scroll.size else 20
        except Exception:
            h = 20
        n = max(0, lp.index - max(1, h))
        if n != lp.index:
            lp.set_index(n)
            self._scroll_list_to(n)
            self.run_cmd_for_index(n)

    def action_output_top(self) -> None:
        try:
            self.query_one("#output-scroll", VerticalScroll).scroll_home(
                animate=False, immediate=True
            )
        except Exception:
            pass

    def action_output_bottom(self) -> None:
        try:
            self.query_one("#output-scroll", VerticalScroll).scroll_end(
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
