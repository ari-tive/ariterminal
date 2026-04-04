"""
Ariterminal — A stylish custom terminal UI built with Textual (Minecraft Logs style)
"""

import os
import subprocess
from datetime import datetime
from typing import Iterable

from rich.text import Text
from textual.app import App
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Input, Label, RichLog

class Toolbar(Widget):
    """Top bar with search and filters."""
    DEFAULT_CSS = """
    Toolbar {
        height: 3;
        layout: horizontal;
        background: #090c10;
        border-bottom: solid #00bcd4;
        padding: 0 1;
        align-vertical: middle;
    }
    #app-logo {
        color: #00bcd4;
        text-style: bold;
        margin-top: 1;
        width: 15;
    }
    #search-input {
        width: 30;
        border: solid #30363d;
        background: #0d1117;
        height: 1;
        padding: 0 1;
        margin-top: 1;
    }
    #search-input:focus {
        border: solid #00bcd4;
    }
    .filter-btn {
        min-width: 8;
        height: 1;
        margin-left: 1;
        border: solid #30363d;
        background: transparent;
        margin-top: 1;
    }
    #btn-error { color: #f85149; border-top: solid #f85149; }
    #btn-warn { color: #d29922; border-top: solid #d29922; }
    #btn-info { color: #00bcd4; border-top: solid #00bcd4; }
    #btn-debug { color: #bc8cff; border-top: solid #bc8cff; }
    #btn-trace { color: #8b949e; border-top: solid #8b949e; }
    #toolbar-spacer { width: 1fr; }
    #btn-settings { color: #8b949e; background: transparent; border: none; min-width: 3; margin-top: 1;}
    """
    def compose(self) -> Iterable[Widget]:
        yield Label(">_ ARITERMINAL", id="app-logo")
        yield Input(placeholder="🔍 Search logs...", id="search-input")
        yield Button("ERROR", id="btn-error", classes="filter-btn")
        yield Button("WARN", id="btn-warn", classes="filter-btn")
        yield Button("INFO", id="btn-info", classes="filter-btn")
        yield Button("DEBUG", id="btn-debug", classes="filter-btn")
        yield Button("TRACE", id="btn-trace", classes="filter-btn")
        yield Label("", id="toolbar-spacer")
        yield Button("⚙", id="btn-settings")

class InstancesPanel(Widget):
    """Right sidebar for instances."""
    DEFAULT_CSS = """
    InstancesPanel {
        width: 20%;
        background: #090c10;
        border-left: solid #00bcd4;
        padding: 1 1;
        layout: vertical;
    }
    #instances-header {
        color: #00bcd4;
        text-style: bold;
        margin-bottom: 1;
        height: 1;
    }
    .instance-card {
        height: 4;
        border: solid #30363d;
        background: #0d1117;
        padding: 0 1;
        margin-bottom: 1;
    }
    .card-title { color: #e6e6e6; text-style: bold; width: 1fr; }
    .card-gear { color: #8b949e; width: 3; text-align: right; }
    .card-subtitle { color: #8b949e; width: 1fr; }
    .card-time { color: #8b949e; width: 6; text-align: right; }
    #instance-spacer { height: 1fr; }
    #instance-status { color: #8b949e; margin-top: 1; height: 1; }
    #bottom-info { height: 1; color: #8b949e; margin-bottom: 1; }
    #info-name { width: 1fr; }
    #info-time { width: 6; text-align: right; }
    #instance-controls { layout: horizontal; height: 3; }
    #btn-start { background: #238636; color: white; border: none; height: 1; margin-right: 1; }
    #btn-folder { background: #30363d; color: white; border: none; height: 1; margin-right: 1; min-width: 4;}
    #btn-stop { background: #30363d; color: #00bcd4; border: none; height: 1; min-width: 4;}
    """
    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="instances-header"):
            yield Label("🖥 Instances")
        with Container(classes="instance-card"):
            with Horizontal():
                yield Label("Fabric 1.21.11", classes="card-title")
                yield Label("⚙", classes="card-gear")
            with Horizontal():
                yield Label("👤 ari-tive", classes="card-subtitle")
                yield Label("⏱ 0:08", classes="card-time")
                
        yield Label("", id="instance-spacer")
        with Horizontal(id="bottom-info"):
            yield Label("Fabric 1.21.11", id="info-name")
            yield Label("0:08", id="info-time")
        with Horizontal(id="instance-controls"):
            yield Button("▶ START", id="btn-start")
            yield Button("📁", id="btn-folder")
            yield Button("⏹", id="btn-stop")
        yield Label("0 RUNNING", id="instance-status")

class StatusBar(Widget):
    """Bottom status bar."""
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        layout: horizontal;
        background: #090c10;
        border-top: solid #00bcd4;
        color: #8b949e;
        padding: 0 1;
    }
    #status-lines { width: 15; }
    #status-following { color: #00bcd4; width: auto; text-style: bold; padding-right: 1; }
    #cmd-input-container {
        height: 1;
        background: transparent;
        layout: horizontal;
        width: 1fr;
    }
    #cmd-prompt { color: #00bcd4; text-style: bold; width: auto; }
    #cmd-input { border: none; background: transparent; height: 1; width: 1fr; padding: 0 1; color: #e6e6e6; }
    #cmd-input:focus { border: none; }
    .status-btn { background: transparent; border: none; color: #8b949e; height: 1; min-width: 10; margin-left: 1; }
    .status-btn:focus { text-style: none; }
    .status-btn:hover { color: #e6e6e6; }
    """
    cmd_count = reactive(0)
    def compose(self) -> Iterable[Widget]:
        yield Label("☰ 0 LINES", id="status-lines")
        yield Label("⬇ FOLLOWING", id="status-following")
        with Horizontal(id="cmd-input-container"):
            yield Label(" ❯", id="cmd-prompt")
            yield Input(id="cmd-input")
        yield Button("🗑 CLEAR", id="btn-clear", classes="status-btn")
        yield Button("📤 UPLOAD", id="btn-upload", classes="status-btn")
        
    def watch_cmd_count(self, count: int) -> None:
        self.query_one("#status-lines", Label).update(f"☰ {count} LINES")

class Ariterminal(App):
    """The main Ariterminal application - Minecraft Log Viewer Style."""
    
    TITLE = "Ariterminal"
    SUB_TITLE = "Your stylish command shell"
    
    CSS = """
    Screen { background: #0d1117; }
    #main-layout { layout: horizontal; height: 1fr; width: 100%; }
    #left-pane { width: 80%; height: 1fr; layout: vertical; }
    #output-log {
        height: 1fr;
        background: #0d1117;
        padding: 0 1;
        scrollbar-size: 1 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+l", "clear_screen", "Clear", show=False),
        Binding("up", "history_prev", "Prev", show=False),
        Binding("down", "history_next", "Next", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.cwd = os.getcwd()
        self.history = []
        self.hist_idx = -1
        self.log_lines = 0

    def compose(self) -> Iterable[Widget]:
        yield Toolbar()
        with Horizontal(id="main-layout"):
            with Vertical(id="left-pane"):
                yield RichLog(id="output-log", highlight=True, markup=True, wrap=True)
            yield InstancesPanel()
        yield StatusBar()

    def _prompt(self) -> str:
        home = os.path.expanduser("~")
        cwd = self.cwd
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        return f" {cwd} ❯"

    def on_mount(self) -> None:
        log = self.query_one("#output-log", RichLog)
        log.write(Text("Initializing log viewer environment...", style="dim"))
        log.write(Text("  |-- textual 0.38.1", style="dim"))
        log.write(Text("  |-- rich 13.6.0", style="dim"))
        log.write(Text("  \\-- psutil 5.9.5", style="dim"))
        log.write(Text("  █████╗ ██████╗ ██╗████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗███████╗██╗     ", style="bold cyan"))
        log.write(Text(" ██╔══██╗██╔══██╗██║╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔════╝██║     ", style="bold cyan"))
        log.write(Text(" ███████║██████╔╝██║   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║█████╗  ██║     ", style="bold blue"))
        log.write(Text(" ██╔══██║██╔══██╗██║   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══╝  ██║     ", style="bold blue"))
        log.write(Text(" ██║  ██║██║  ██║██║   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║███████╗███████╗", style="bold magenta"))
        log.write(Text(" ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝", style="bold magenta"))
        log.write(Text("- Ariterminal system READY", style="dim"))
        self.log_lines += 11
        self.query_one(StatusBar).cmd_count = self.log_lines
        self.query_one("#cmd-prompt", Label).update(self._prompt())
        self.query_one("#cmd-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return

        self.history.append(cmd)
        self.hist_idx = len(self.history)

        log = self.query_one("#output-log", RichLog)
        log.write(Text(f"- [{datetime.now().strftime('%H:%M:%S')}] Executing: {cmd}", style="bold cyan"))
        self.log_lines += 1

        self.query_one("#cmd-input", Input).value = ""
        self._run_command(cmd, log)

        self.query_one(StatusBar).cmd_count = self.log_lines
        self.query_one("#cmd-prompt", Label).update(self._prompt())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-clear":
            self.action_clear_screen()

    def _format_output_lines(self, text_output: str, is_err: bool = False) -> None:
        log = self.query_one("#output-log", RichLog)
        lines = text_output.splitlines()
        style = "bold red" if is_err else "e6e6e6"
        for i, line in enumerate(lines):
            prefix = "  |-- " if i < len(lines) - 1 else "  \\-- "
            log.write(Text(prefix + line, style=style))
            self.log_lines += 1

    def _run_command(self, cmd: str, log: RichLog) -> None:
        parts = cmd.strip().split()
        base = parts[0].lower() if parts else ""

        if base == "help":
            help_text = "Available commands:\nhelp - Show help\nclear - Clear output\nhistory - Show history\nexit - Quit\ncd - Change directory"
            self._format_output_lines(help_text)
            return

        if base == "clear":
            self.action_clear_screen()
            return

        if base == "exit":
            self.exit()
            return

        if base == "history":
            if not self.history:
                self._format_output_lines("No history yet.", True)
            else:
                hist_str = "\n".join([f"{i}. {h}" for i, h in enumerate(self.history, 1)])
                self._format_output_lines(hist_str)
            return

        if base == "cd":
            target = " ".join(parts[1:]) if len(parts) > 1 else os.path.expanduser("~")
            try:
                os.chdir(target)
                self.cwd = os.getcwd()
                self._format_output_lines(f"Changed directory to: {self.cwd}")
            except Exception as e:
                self._format_output_lines(f"cd: {e}", True)
            return

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
                self._format_output_lines(result.stdout.rstrip())
            if result.stderr:
                self._format_output_lines(result.stderr.rstrip(), True)
            if not result.stdout and not result.stderr:
                self._format_output_lines("(no output)")
        except subprocess.TimeoutExpired:
            self._format_output_lines("Command timed out after 30s.", True)
        except Exception as e:
            self._format_output_lines(f"Error: {e}", True)

    def action_clear_screen(self) -> None:
        self.query_one("#output-log", RichLog).clear()
        self.log_lines = 0
        self.query_one(StatusBar).cmd_count = self.log_lines

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
    Ariterminal().run()