"""
NeoTerm — A stylish custom terminal UI built with Textual
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static, Label
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.binding import Binding
from textual.widget import Widget
from rich.text import Text
from datetime import datetime
import subprocess
import os
import platform
import psutil


class SidebarPanel(Widget):
    """Left sidebar showing info & quick stats."""

    DEFAULT_CSS = """
    SidebarPanel {
        width: 28;
        background: $surface;
        border-right: solid $primary-darken-2;
        padding: 1 1;
    }
    SidebarPanel Label {
        color: $text-muted;
        margin-bottom: 1;
    }
    SidebarPanel .section-title {
        color: $accent;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }
    """

    cwd = reactive(os.getcwd)
    cmd_count = reactive(0)

    def compose(self) -> ComposeResult:
        yield Label("◈ NeoTerm", classes="section-title")
        yield Label("─" * 22)
        yield Label("📂 Directory", classes="section-title")
        yield Label(self._short_cwd(), id="sidebar-cwd")
        yield Label("")
        yield Label("⚡ Session", classes="section-title")
        yield Label("0 commands run", id="sidebar-cmdcount")
        yield Label("")
        yield Label("💻 System", classes="section-title")
        yield Label(f"OS: {platform.system()}", id="sidebar-os")
        yield Label(f"CPU: {psutil.cpu_percent()}%", id="sidebar-cpu")
        yield Label(f"RAM: {psutil.virtual_memory().percent}%", id="sidebar-ram")
        yield Label("")
        yield Label("⏰ Time", classes="section-title")
        yield Label("", id="sidebar-time")

    def _short_cwd(self) -> str:
        cwd = str(self.cwd)
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        if len(cwd) > 22:
            cwd = "…" + cwd[-21:]
        return cwd

    def on_mount(self) -> None:
        self.set_interval(2, self._refresh_stats)

    def _refresh_stats(self) -> None:
        self.query_one("#sidebar-time", Label).update(
            datetime.now().strftime("%H:%M:%S")
        )
        self.query_one("#sidebar-cpu", Label).update(
            f"CPU: {psutil.cpu_percent()}%"
        )
        self.query_one("#sidebar-ram", Label).update(
            f"RAM: {psutil.virtual_memory().percent}%"
        )

    def watch_cwd(self, cwd: str) -> None:
        self.query_one("#sidebar-cwd", Label).update(self._short_cwd())

    def watch_cmd_count(self, count: int) -> None:
        self.query_one("#sidebar-cmdcount", Label).update(
            f"{count} command{'s' if count != 1 else ''} run"
        )


class NeoTerm(App):
    """The main NeoTerm application."""

    TITLE = "NeoTerm"
    SUB_TITLE = "Your stylish command shell"

    CSS = """
    Screen {
        background: $background;
    }
    #main-layout {
        height: 1fr;
    }
    #right-pane {
        height: 1fr;
    }
    #output-log {
        height: 1fr;
        border: solid $primary-darken-3;
        background: $surface-darken-1;
        padding: 0 1;
        margin: 0 1 0 0;
    }
    #input-row {
        height: 3;
        margin: 0 1 0 0;
        background: $surface;
        border: solid $accent;
    }
    #prompt-label {
        width: auto;
        padding: 1 1;
        color: $accent;
        text-style: bold;
    }
    #cmd-input {
        border: none;
        background: transparent;
        height: 1fr;
    }
    #cmd-input:focus {
        border: none;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_screen", "Clear", show=True),
        Binding("up", "history_prev", "Prev", show=False),
        Binding("down", "history_next", "Next", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.cwd = os.getcwd()
        self.history = []
        self.hist_idx = -1
        self.cmd_count = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            yield SidebarPanel()
            with Vertical(id="right-pane"):
                yield RichLog(id="output-log", highlight=True, markup=True, wrap=True)
                with Horizontal(id="input-row"):
                    yield Label(self._prompt(), id="prompt-label")
                    yield Input(placeholder="Type a command...", id="cmd-input")
        yield Footer()

    def _prompt(self) -> str:
        home = os.path.expanduser("~")
        cwd = self.cwd
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        return f" {cwd} ❯ "

    def on_mount(self) -> None:
        log = self.query_one("#output-log", RichLog)
        log.write(Text(""))
        log.write(Text("  ███╗   ██╗███████╗ ██████╗ ████████╗███████╗██████╗ ███╗   ███╗", style="bold cyan"))
        log.write(Text("  ████╗  ██║██╔════╝██╔═══██╗╚══██╔══╝██╔════╝██╔══██╗████╗ ████║", style="bold cyan"))
        log.write(Text("  ██╔██╗ ██║█████╗  ██║   ██║   ██║   █████╗  ██████╔╝██╔████╔██║", style="bold blue"))
        log.write(Text("  ██║╚██╗██║██╔══╝  ██║   ██║   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║", style="bold blue"))
        log.write(Text("  ██║ ╚████║███████╗╚██████╔╝   ██║   ███████╗██║  ██║██║ ╚═╝ ██║", style="bold magenta"))
        log.write(Text("  ╚═╝  ╚═══╝╚══════╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝", style="bold magenta"))
        log.write(Text(""))
        log.write(Text("  Welcome to NeoTerm! Type 'help' to see available commands.", style="bold green"))
        log.write(Text(""))
        self.query_one("#cmd-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return

        self.history.append(cmd)
        self.hist_idx = len(self.history)
        self.cmd_count += 1

        log = self.query_one("#output-log", RichLog)
        log.write(Text(f"\n❯ {cmd}", style="bold yellow"))

        self.query_one("#cmd-input", Input).value = ""
        self._run_command(cmd, log)

        sidebar = self.query_one(SidebarPanel)
        sidebar.cmd_count = self.cmd_count
        sidebar.cwd = self.cwd

    def _run_command(self, cmd: str, log: RichLog) -> None:
        parts = cmd.strip().split()
        base = parts[0].lower() if parts else ""

        # ── Built-in commands ──────────────────────────────────────
        if base == "help":
            log.write(Text("Available commands:", style="bold green"))
            builtins = {
                "help":    "Show this help message",
                "clear":   "Clear the terminal output  (Ctrl+L)",
                "history": "Show command history",
                "sysinfo": "Display system information",
                "exit":    "Quit NeoTerm  (Ctrl+C)",
                "cd":      "Change directory  — cd <path>",
            }
            for name, desc in builtins.items():
                log.write(Text(f"  {name:<12} {desc}", style="cyan"))
            log.write(Text("  + any standard CMD command (dir, ping, ipconfig...)", style="dim"))
            return

        if base == "clear":
            self.action_clear_screen()
            return

        if base == "exit":
            self.exit()
            return

        if base == "history":
            if not self.history:
                log.write(Text("No history yet.", style="dim"))
            else:
                for i, h in enumerate(self.history, 1):
                    log.write(Text(f"  {i:>3}.  {h}", style="cyan"))
            return

        if base == "sysinfo":
            mem = psutil.virtual_memory()
            log.write(Text(f"  OS       : {platform.system()} {platform.version()}", style="cyan"))
            log.write(Text(f"  CPU      : {psutil.cpu_percent()}%", style="cyan"))
            log.write(Text(f"  RAM      : {mem.percent}%  ({mem.used // 1024**2} MB / {mem.total // 1024**2} MB)", style="cyan"))
            log.write(Text(f"  Python   : {platform.python_version()}", style="cyan"))
            log.write(Text(f"  CWD      : {self.cwd}", style="cyan"))
            return

        if base == "cd":
            target = " ".join(parts[1:]) if len(parts) > 1 else os.path.expanduser("~")
            try:
                os.chdir(target)
                self.cwd = os.getcwd()
                self.query_one("#prompt-label", Label).update(self._prompt())
                log.write(Text(f"  → {self.cwd}", style="green"))
            except Exception as e:
                log.write(Text(f"  cd: {e}", style="bold red"))
            return

        # ── Shell passthrough ──────────────────────────────────────
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.cwd,
                timeout=30,
            )
            if result.stdout:
                log.write(Text(result.stdout.rstrip()))
            if result.stderr:
                log.write(Text(result.stderr.rstrip(), style="bold red"))
            if not result.stdout and not result.stderr:
                log.write(Text("  (no output)", style="dim"))
        except subprocess.TimeoutExpired:
            log.write(Text("  Command timed out after 30s.", style="bold red"))
        except Exception as e:
            log.write(Text(f"  Error: {e}", style="bold red"))

    def action_clear_screen(self) -> None:
        self.query_one("#output-log", RichLog).clear()

    def action_history_prev(self) -> None:
        if self.history and self.hist_idx > 0:
            self.hist_idx -= 1
            self.query_one("#cmd-input", Input).value = self.history[self.hist_idx]

    def action_history_next(self) -> None:
        if self.hist_idx < len(self.history) - 1:
            self.hist_idx += 1
            self.query_one("#cmd-input", Input).value = self.history[self.hist_idx]
        else:
            self.hist_idx = len(self.history)
            self.query_one("#cmd-input", Input).value = ""


if __name__ == "__main__":
    NeoTerm().run()