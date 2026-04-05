import customtkinter as ctk
import os
import subprocess
from datetime import datetime
import threading
from typing import Optional
import tkinter as tk
from tkinter import colorchooser, simpledialog, font as tkfont

# Set High DPI Awareness for Sharp Text on Windows
try:
    from ctypes import windll
    # 1 = PROCESS_SYSTEM_DPI_AWARE
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)
        self.tw = None

    def enter(self, event=None):
        if self.widget.winfo_class() != "Frame" and self.widget.cget("state") != "disabled":
            pass # Keep going, disabled widgets don't trigger events but frames do.
            
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') and self.widget.bbox("insert") else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"), fg="black")
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

def find_git_bash():
    paths = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        r"D:\Git\bin\bash.exe",
        r"D:\Program Files\Git\bin\bash.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\bash.exe")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def find_powershell():
    """Find PowerShell 7 (pwsh.exe) first, fall back to PowerShell 5."""
    ps7_paths = [
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        r"C:\Program Files (x86)\PowerShell\7\pwsh.exe",
    ]
    for p in ps7_paths:
        if os.path.exists(p):
            return p, "7"
    # Fallback to PowerShell 5
    ps5 = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    if os.path.exists(ps5):
        return ps5, "5"
    return None, None



# ─── Color Constants ───────────────────────────────────────
BG_COLOR = "#0d1117"
SURFACE_COLOR = "#161b22"
CARD_COLOR = "#1c2333"
ACCENT_COLOR = "#00bcd4"
ACCENT_HOVER = "#008ba3"
TEXT_COLOR = "#c9d1d9"
DIM_COLOR = "#6e7681"
BORDER_COLOR = "#30363d"
GREEN_COLOR = "#3fb950"
RED_COLOR = "#f85149"
YELLOW_COLOR = "#d29922"
PURPLE_COLOR = "#bc8cff"
BLUE_COLOR = "#58a6ff"


# Log Levels Configuration
LOG_LEVEL_MAP = {
    "ERROR": {"color": RED_COLOR, "keywords": ["ERROR", "FAILED", "EXCEPTION"]},
    "WARN": {"color": YELLOW_COLOR, "keywords": ["WARN", "WARNING"]},
    "INFO": {"color": BLUE_COLOR, "keywords": ["INFO", "SUCCESS", "READY"]},
    "DEBUG": {"color": ACCENT_COLOR, "keywords": ["DEBUG"]},
    "TRACE": {"color": PURPLE_COLOR, "keywords": ["TRACE"]}
}


class Session:
    def __init__(self, session_id, name, is_admin, cwd, shell_type="CMD", bash_path=None, ps_path=None):
        self.id = session_id
        self.name = name
        self.is_admin = is_admin
        self.cwd = cwd
        self.shell_type = shell_type
        self.bash_path = bash_path
        self.ps_path = ps_path
        # Color per shell type
        if shell_type == "Git Bash":
            self.color = "#f05133"
        elif shell_type == "PowerShell":
            self.color = "#012456"
        elif is_admin:
            self.color = RED_COLOR
        else:
            self.color = ACCENT_COLOR
        self.group = "Default"
        self.logs = [] # Structured logs: list[dict]
        self.log_count = 0
        self.start_time = datetime.now()
        self.history = []


class SessionCard(ctk.CTkFrame):
    """A richly themed session card with color accent bar, status dot, and uptime."""

    def __init__(self, parent, session, is_active, on_click, on_context):
        bg = CARD_COLOR if not is_active else SURFACE_COLOR
        border = session.color if is_active else BORDER_COLOR
        super().__init__(parent, fg_color=bg, border_width=2 if is_active else 1, 
                         border_color=border, corner_radius=2)

        self.session = session

        # Make entire card clickable
        self.bind("<Button-1>", lambda e: on_click(session.id))
        self.bind("<Button-3>", lambda e: on_context(e, session.id))

        # ── Inner layout ──
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        inner.bind("<Button-1>", lambda e: on_click(session.id))
        inner.bind("<Button-3>", lambda e: on_context(e, session.id))

        # Top row: status dot + name
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")
        top_row.bind("<Button-1>", lambda e: on_click(session.id))
        top_row.bind("<Button-3>", lambda e: on_context(e, session.id))

        dot_color = GREEN_COLOR if is_active else DIM_COLOR
        dot = ctk.CTkLabel(top_row, text="●", font=("Roboto", 12), text_color=dot_color, width=12)




        dot.pack(side="left", padx=(0, 6))
        dot.bind("<Button-1>", lambda e: on_click(session.id))
        dot.bind("<Button-3>", lambda e: on_context(e, session.id))

        name_text = f"{session.name}"
        if session.is_admin:
            name_text = f"🛡️ {name_text}"
        name_label = ctk.CTkLabel(top_row, text=name_text, font=("Roboto", 14, "bold"), 

                                  text_color=session.color)



        name_label.pack(side="left", fill="x", expand=True)
        name_label.bind("<Button-1>", lambda e: on_click(session.id))
        name_label.bind("<Button-3>", lambda e: on_context(e, session.id))

        if session.shell_type == "Git Bash":
            tag_label = ctk.CTkLabel(top_row, text="BASH", font=("Roboto", 10, "bold"), text_color=BG_COLOR, fg_color="#f05133", corner_radius=4, width=40)
            tag_label.pack(side="right", padx=(5, 0))
            tag_label.bind("<Button-1>", lambda e: on_click(session.id))
            tag_label.bind("<Button-3>", lambda e: on_context(e, session.id))
        elif session.shell_type == "PowerShell":
            tag_label = ctk.CTkLabel(top_row, text="PS", font=("Roboto", 10, "bold"), text_color="#c9d1d9", fg_color="#012456", corner_radius=4, width=28)
            tag_label.pack(side="right", padx=(5, 0))
            tag_label.bind("<Button-1>", lambda e: on_click(session.id))
            tag_label.bind("<Button-3>", lambda e: on_context(e, session.id))
        elif session.is_admin:
            tag_label = ctk.CTkLabel(top_row, text="ADMIN", font=("Roboto", 10, "bold"), text_color=BG_COLOR, fg_color=RED_COLOR, corner_radius=4, width=46)
            tag_label.pack(side="right", padx=(5, 0))
            tag_label.bind("<Button-1>", lambda e: on_click(session.id))
            tag_label.bind("<Button-3>", lambda e: on_context(e, session.id))
        else:
            tag_label = ctk.CTkLabel(top_row, text="CMD", font=("Roboto", 10, "bold"), text_color=DIM_COLOR, fg_color=BORDER_COLOR, corner_radius=4, width=34)
            tag_label.pack(side="right", padx=(5, 0))
            tag_label.bind("<Button-1>", lambda e: on_click(session.id))
            tag_label.bind("<Button-3>", lambda e: on_context(e, session.id))

        # Bottom row: directory + uptime
        bottom_row = ctk.CTkFrame(inner, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(5, 0))
        bottom_row.bind("<Button-1>", lambda e: on_click(session.id))
        bottom_row.bind("<Button-3>", lambda e: on_context(e, session.id))

        short_cwd = session.cwd
        home = os.path.expanduser("~")
        if short_cwd.startswith(home):
            short_cwd = short_cwd.replace(home, "~")

        dir_label = ctk.CTkLabel(bottom_row, text=f"📁 {short_cwd}", font=("Roboto", 12), text_color=DIM_COLOR)




        dir_label.pack(side="left")
        dir_label.bind("<Button-1>", lambda e: on_click(session.id))
        dir_label.bind("<Button-3>", lambda e: on_context(e, session.id))

        delta = datetime.now() - session.start_time
        mins, secs = divmod(int(delta.total_seconds()), 60)
        hours, mins = divmod(mins, 60)
        uptime_str = f"{hours:02}:{mins:02}:{secs:02}"
        
        uptime_label = ctk.CTkLabel(bottom_row, text=f"⏱ {uptime_str}", font=("Roboto", 12), text_color=DIM_COLOR)




        uptime_label.pack(side="right")
        uptime_label.bind("<Button-1>", lambda e: on_click(session.id))
        uptime_label.bind("<Button-3>", lambda e: on_context(e, session.id))


class NewSessionDialog(ctk.CTkToplevel):
    SHELL_OPTIONS = [
        {"key": "CMD",        "icon": "🖥️", "title": "CMD",           "desc": "Command Prompt\nStandard shell",       "is_admin": False, "shell": "CMD"},
        {"key": "CMD_ADMIN",  "icon": "🛡️", "title": "CMD (Admin)",   "desc": "Elevated privileges\nRun as Admin",     "is_admin": True,  "shell": "CMD"},
        {"key": "PS",         "icon": "💙", "title": "PowerShell",    "desc": "PowerShell 5/7\nAdvanced scripting",   "is_admin": False, "shell": "PowerShell"},
        {"key": "BASH",       "icon": "🟠", "title": "Git Bash",      "desc": "Unix-style shell\nGit & bash commands", "is_admin": False, "shell": "Git Bash"},
    ]

    def __init__(self, parent, on_create):
        super().__init__(parent)
        self.title("New Session")
        self.geometry("480x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_create = on_create
        self.parent = parent
        self.configure(fg_color=SURFACE_COLOR)
        self.selected_key = "CMD"
        self.card_frames = {}

        # Detect available shells
        self.bash_path = find_git_bash()
        self.ps_path, self.ps_version = find_powershell()

        # Center and size
        width, height = 480, 460
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        self.geometry(f"{width}x{height}+{px + (pw // 2) - (width // 2)}+{py + (ph // 2) - (height // 2)}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 5), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        
        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack()
        ctk.CTkLabel(header_inner, text="⚡", font=("Roboto", 18)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header_inner, text="NEW SESSION", font=("Roboto", 18, "bold"), text_color=ACCENT_COLOR).pack(side="left")

        ctk.CTkLabel(self, text="Choose your shell type", font=("Roboto", 12), text_color=DIM_COLOR).grid(row=1, column=0, pady=(0, 12), sticky="ew")

        # ── 2x2 Card Grid ──
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.grid(row=2, column=0, padx=30, sticky="nsew")
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)

        for idx, opt in enumerate(self.SHELL_OPTIONS):
            row_pos = idx // 2
            col_pos = idx % 2

            is_disabled = (opt["key"] == "BASH" and not self.bash_path)

            card = ctk.CTkFrame(grid_frame, fg_color=CARD_COLOR, border_width=2, 
                                border_color=BORDER_COLOR, corner_radius=6, width=195, height=95)
            card.grid(row=row_pos, column=col_pos, padx=5, pady=5, sticky="nsew")
            card.grid_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=10)

            title_row = ctk.CTkFrame(inner, fg_color="transparent")
            title_row.pack(fill="x")

            icon_color = DIM_COLOR if is_disabled else TEXT_COLOR
            ctk.CTkLabel(title_row, text=opt["icon"], font=("Roboto", 16), text_color=icon_color).pack(side="left", padx=(0, 6))
            
            title_color = DIM_COLOR if is_disabled else TEXT_COLOR
            ctk.CTkLabel(title_row, text=opt["title"], font=("Roboto", 14, "bold"), text_color=title_color).pack(side="left")

            desc_color = BORDER_COLOR if is_disabled else DIM_COLOR
            desc_text = "Not installed" if is_disabled else opt["desc"]
            ctk.CTkLabel(inner, text=desc_text, font=("Roboto", 11), text_color=desc_color, 
                         justify="left", anchor="w").pack(fill="x", pady=(4, 0))

            self.card_frames[opt["key"]] = card

            if is_disabled:
                ToolTip(card, "Git Bash not found. Install from git-scm.com")
            else:
                # Make card clickable
                key = opt["key"]
                # Bind all descendants too
                def bind_recursive(widget, k):
                    widget.bind("<Button-1>", lambda e: self._select_card(k))
                    for child in widget.winfo_children():
                        bind_recursive(child, k)
                
                bind_recursive(card, key)

        # ── Session Name Entry ──
        self.name_entry = ctk.CTkEntry(self, placeholder_text="Session Name", width=420, height=38,
                                       fg_color=BG_COLOR, border_color=BORDER_COLOR, corner_radius=2, font=("Roboto", 14))
        self.name_entry.grid(row=3, column=0, pady=(15, 8), sticky="ew", padx=30)

        session_num = len(parent.sessions) + 1
        self.name_entry.insert(0, f"CMD Session {session_num}")

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, pady=(8, 20), padx=30, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_frame, text="CANCEL", height=40, fg_color="transparent",
                      border_width=1, border_color=BORDER_COLOR, text_color=DIM_COLOR, corner_radius=2,
                      hover=False, command=self.destroy).grid(row=0, column=0, padx=5, sticky="ew")

        ctk.CTkButton(btn_frame, text="⚡ CREATE SESSION", height=40, fg_color=ACCENT_COLOR,
                      hover=False, text_color=BG_COLOR, font=("Roboto", 14, "bold"),
                      corner_radius=2, command=self._on_confirm).grid(row=0, column=1, padx=5, sticky="ew")

        # Highlight default selection
        self._select_card("CMD")

    def _select_card(self, key):
        self.selected_key = key
        # Update border colors
        for k, card in self.card_frames.items():
            if k == key:
                card.configure(border_color=ACCENT_COLOR)
            else:
                card.configure(border_color=BORDER_COLOR)
        # Auto-fill name
        session_num = len(self.parent.sessions) + 1
        name_map = {"CMD": "CMD", "CMD_ADMIN": "Admin", "PS": "PowerShell", "BASH": "Git Bash"}
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, f"{name_map[key]} Session {session_num}")

    def _on_confirm(self):
        name = self.name_entry.get().strip() or "Session"
        opt = next(o for o in self.SHELL_OPTIONS if o["key"] == self.selected_key)
        is_admin = opt["is_admin"]
        shell_type = opt["shell"]
        self.on_create(name, is_admin, shell_type, self.bash_path, self.ps_path)
        self.destroy()


class LogSettingsPopup(ctk.CTkToplevel):
    def __init__(self, parent, button_widget):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color=BG_COLOR)
        self.parent = parent
        
        # Position relative to button
        self.update_idletasks()
        x = button_widget.winfo_rootx()
        y = button_widget.winfo_rooty() + button_widget.winfo_height() + 5
        # Align right edge with button right edge if possible
        self.geometry(f"280x140+{x - 240}+{y}")
        
        border_frame = ctk.CTkFrame(self, fg_color=BG_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        border_frame.pack(fill="both", expand=True)

        header = ctk.CTkLabel(border_frame, text="LOG SETTINGS", font=("Roboto", 16, "bold"), 

                              text_color=TEXT_COLOR, anchor="w")



        header.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkFrame(border_frame, height=1, fg_color=BORDER_COLOR).pack(fill="x", padx=15, pady=5)

        row = ctk.CTkFrame(border_frame, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=10)

        self.switch = ctk.CTkSwitch(row, text="", width=45,
                                     fg_color="#2b2b2b", progress_color=ACCENT_COLOR,
                                     command=self.toggle_prefix)
        self.switch.pack(side="left")
        if parent.show_thread_prefix:
            self.switch.select()
        
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", padx=12)
        
        ctk.CTkLabel(text_frame, text="Thread Prefix", font=("Roboto", 14, "bold"), 
                     text_color=TEXT_COLOR, anchor="w").pack(fill="x")
        ctk.CTkLabel(text_frame, text="Show [Thread/LEVEL] prefix", font=("Roboto", 12), 

                     text_color=DIM_COLOR, anchor="w").pack(fill="x")




        self.bind("<FocusOut>", lambda e: self.destroy())
        self.focus_set()

    def toggle_prefix(self):
        self.parent.show_thread_prefix = self.switch.get() == 1
        self.parent.refresh_output()



class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.on_confirm = on_confirm
        
        # Center the dialog
        self.geometry("340x180")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE_COLOR)
        
        # Ensure it's on top and modal-like
        self.attributes("-topmost", True)
        self.grab_set()
        
        # Layout
        border_frame = ctk.CTkFrame(self, fg_color=BG_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        border_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        header = ctk.CTkLabel(border_frame, text="⚠️ CONFIRMATION", font=("Roboto", 16, "bold"), 
                              text_color=ACCENT_COLOR, anchor="w")
        header.pack(fill="x", padx=20, pady=(15, 10))
        
        msg_label = ctk.CTkLabel(border_frame, text=message, font=("Roboto", 14), 
                                 text_color=TEXT_COLOR, wraplength=280)
        msg_label.pack(fill="x", padx=20, pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(border_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkButton(btn_frame, text="NO", width=90, height=34, fg_color=CARD_COLOR,
                      hover=False, text_color=TEXT_COLOR, font=("Roboto", 14, "bold"),
                      corner_radius=2, command=self.destroy).pack(side="left", padx=8)

        ctk.CTkButton(btn_frame, text="YES", width=110, height=34, fg_color=ACCENT_COLOR,
                      hover=False, text_color=BG_COLOR, font=("Roboto", 14, "bold"),
                      corner_radius=2, command=self._on_confirm).pack(side="left", padx=8)

    def _on_confirm(self):
        self.on_confirm()
        self.destroy()

class Ariterminal(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ariterminal")
        self.geometry("1200x800")
        self.configure(fg_color=BG_COLOR)
        
        # Load Roboto Regular font using Windows API
        try:
            import ctypes
            import sys
            # Resolve font path for PyInstaller bundle
            if getattr(sys, 'frozen', False):
                font_path = os.path.join(sys._MEIPASS, 'Roboto-Regular.ttf')
            else:
                font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Roboto-Regular.ttf')
            # FR_PRIVATE = 0x10 — only this process can see the font
            ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
        except Exception:
            pass  # Fallback to default if font fails to load




        self.cwd = os.getcwd()
        self.sessions: dict[str, Session] = {}
        self.active_session_id: Optional[str] = None
        self.log_count = 0
        self.menu_session_target: Optional[str] = None
        
        # Search state
        self.search_matches: list[str] = []  # list of text indices
        self.current_match_index = -1
        
        # Log settings
        self.show_thread_prefix = False
        
        # Filter State
        self.active_filters = {level: True for level in LOG_LEVEL_MAP.keys()}
        self.filter_btns = {}

        ctk.set_appearance_mode("dark")


        self.setup_ui()
        self.update_uptime()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ─── TOP BAR ──────────────────────────────────────
        self.top_bar = ctk.CTkFrame(self, height=56, fg_color=SURFACE_COLOR, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(self.top_bar, text=">_ ARITERMINAL", 
                                        font=("Roboto", 18, "bold"), text_color=ACCENT_COLOR)




        self.title_label.grid(row=0, column=0, padx=25, pady=14)

        # Search bar + controls
        self.search_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.search_frame.grid(row=0, column=1, padx=10)

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="🔍 Search logs...", width=300, height=34,
                                         fg_color=BG_COLOR, border_color=BORDER_COLOR, corner_radius=2, font=("Roboto", 14))




        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", lambda e: self.perform_search())
        self.search_entry.bind("<Escape>", lambda e: self.clear_search())

        self.search_count_label = ctk.CTkLabel(self.search_frame, text="", font=("Consolas", 10),
                                               text_color=DIM_COLOR, width=90)
        self.search_count_label.pack(side="left", padx=(0, 4))

        self.search_up_btn = ctk.CTkButton(self.search_frame, text="▲", width=28, height=28,
                                           fg_color=CARD_COLOR, hover=False, text_color=TEXT_COLOR,
                                           font=("Roboto", 12), corner_radius=2,
                                           command=lambda: self.navigate_search(-1))




        self.search_up_btn.pack(side="left", padx=1)

        self.search_down_btn = ctk.CTkButton(self.search_frame, text="▼", width=28, height=28,
                                             fg_color=CARD_COLOR, hover=False, text_color=TEXT_COLOR,
                                             font=("Roboto", 12), corner_radius=2,

                                             command=lambda: self.navigate_search(1))



        self.search_down_btn.pack(side="left", padx=1)

        self.settings_btn = ctk.CTkButton(self.search_frame, text="⚙", width=34, height=34,
                                          fg_color=CARD_COLOR, hover=False, text_color=ACCENT_COLOR,
                                          font=("Roboto", 16, "bold"), corner_radius=2,

                                          command=lambda: LogSettingsPopup(self, self.settings_btn))



        self.settings_btn.pack(side="left", padx=(10, 0))


        self.filter_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.filter_frame.grid(row=0, column=2, padx=15)

        for i, (level, config) in enumerate(LOG_LEVEL_MAP.items()):
            color = config["color"]
            btn = ctk.CTkButton(self.filter_frame, text=level, width=65, height=28,
                                fg_color="#1a1a1a", border_color=color, border_width=1,
                                text_color=color, hover=False,
                                font=("Roboto", 14), corner_radius=2,

                                command=lambda l=level: self.toggle_filter(l))




            btn.grid(row=0, column=i, padx=3)
            self.filter_btns[level] = btn



        # ─── MAIN AREA ────────────────────────────────────
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(12, 8))
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, minsize=260)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.output_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.output_container.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.output_container.grid_columnconfigure(0, weight=1)
        self.output_container.grid_rowconfigure(0, weight=1)

        self.output_text = ctk.CTkTextbox(self.output_container, font=("Roboto", 15), fg_color=BG_COLOR,

                                          text_color=TEXT_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=2)



        self.output_text.configure(state="disabled")

        self.welcome_frame = ctk.CTkFrame(self.output_container, fg_color=BG_COLOR, border_width=1, 
                                          border_color=BORDER_COLOR, corner_radius=2)

        self.welcome_frame.grid(row=0, column=0, sticky="nsew")

        self.welcome_inner = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        self.welcome_inner.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(self.welcome_inner, text="⚡", font=("Roboto", 28)).pack(pady=(0, 10))
        ctk.CTkLabel(self.welcome_inner, text="No active sessions", font=("Roboto", 20, "bold"), 
                     text_color=TEXT_COLOR).pack(pady=(0, 6))
        ctk.CTkLabel(self.welcome_inner, text="Create a new terminal session to get started",
                     font=("Roboto", 14), text_color=DIM_COLOR).pack(pady=(0, 30))

        ctk.CTkButton(self.welcome_inner, text="⚡ New Session", fg_color=ACCENT_COLOR, hover=False,
                      text_color=BG_COLOR, font=("Roboto", 14, "bold"), height=48, width=220, corner_radius=2,

                      command=self.open_new_session_dialog).pack()




        # ─── RIGHT PANEL ──────────────────────────────────
        self.instances_panel = ctk.CTkFrame(self.main_container, fg_color=SURFACE_COLOR, border_width=1, 
                                            border_color=BORDER_COLOR, corner_radius=2, width=260)

        self.instances_panel.grid(row=0, column=1, sticky="nsew")

        self.inst_header = ctk.CTkFrame(self.instances_panel, fg_color="transparent")
        self.inst_header.pack(fill="x", padx=14, pady=(14, 8))

        self.inst_title = ctk.CTkLabel(self.inst_header, text="🖥  INSTANCES", 
                                       font=("Roboto", 14, "bold"), text_color=ACCENT_COLOR)




        self.inst_title.pack(side="left")

        self.session_count_badge = ctk.CTkLabel(self.inst_header, text="0", width=24, height=20,
                                                 fg_color=BORDER_COLOR, corner_radius=10,
                                                 font=("Roboto", 12, "bold"), text_color=DIM_COLOR)




        self.session_count_badge.pack(side="left", padx=(8, 0))

        self.add_session_btn = ctk.CTkButton(self.inst_header, text="+", width=30, height=30,
                                              fg_color=ACCENT_COLOR, hover=False,
                                              text_color=BG_COLOR, font=("Roboto", 16, "bold"),

                                              corner_radius=2, command=self.open_new_session_dialog)



        self.add_session_btn.pack(side="right")

        sep = ctk.CTkFrame(self.instances_panel, height=1, fg_color=BORDER_COLOR)
        sep.pack(fill="x", padx=14, pady=(0, 4))

        self.session_scroll = ctk.CTkScrollableFrame(self.instances_panel, fg_color="transparent", border_width=0)
        self.session_scroll.pack(fill="both", expand=True, padx=6, pady=4)

        # ─── BOTTOM BAR ────────────────────────────────────
        self.bottom_bar = ctk.CTkFrame(self, height=44, fg_color=SURFACE_COLOR, corner_radius=0)
        self.bottom_bar.grid(row=2, column=0, sticky="ew")
        self.bottom_bar.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(self.bottom_bar, text="☰ 0 LINES", width=100, text_color=DIM_COLOR, 
                                         font=("Roboto", 12, "bold"))




        self.status_label.grid(row=0, column=0, padx=15)

        self.active_session_label = ctk.CTkLabel(self.bottom_bar, text="", font=("Roboto", 12, "bold"), text_color=ACCENT_COLOR)




        self.active_session_label.grid(row=0, column=1, sticky="w", padx=5)

        self.input_frame = ctk.CTkFrame(self.bottom_bar, fg_color=BG_COLOR, border_width=1, 
                                        border_color=BORDER_COLOR, corner_radius=2)

        self.input_frame.grid(row=0, column=2, sticky="ew", padx=15, pady=6)

        ctk.CTkLabel(self.input_frame, text="❯", text_color=ACCENT_COLOR, 
                     font=("Roboto", 14, "bold")).pack(side="left", padx=(10, 4))





        self.command_entry = ctk.CTkEntry(self.input_frame, fg_color="transparent", border_width=0,
                                          text_color=TEXT_COLOR, font=("Roboto", 16), 

                                          placeholder_text="Enter command...", height=30)



        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.command_entry.bind("<Return>", self.on_enter)

        self.clear_btn = ctk.CTkButton(self.bottom_bar, text="🗑 CLEAR", width=85, height=28, fg_color="transparent",
                                       text_color=DIM_COLOR, hover=False, corner_radius=2, command=self.clear_logs)

        self.clear_btn.grid(row=0, column=3, padx=(0, 15))

        # ─── CONTEXT MENU ──────────────────────────────────
        self.context_menu = tk.Menu(self, tearoff=0, bg=SURFACE_COLOR, fg=TEXT_COLOR,
                                    activebackground=ACCENT_COLOR, activeforeground=BG_COLOR,
                                    font=("Roboto", 12), relief="flat", bd=1)




        self.context_menu.add_command(label="  ✏️  Rename", command=self.menu_rename)
        self.context_menu.add_command(label="  🎨  Set Color", command=self.menu_set_color)
        self.context_menu.add_command(label="  📁  Group", command=self.menu_group)
        self.context_menu.add_command(label="  📋  Duplicate", command=self.menu_duplicate)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="  ❌  Close Session", command=self.menu_close)

        # Define tag colors
        for level, config in LOG_LEVEL_MAP.items():
            self.output_text._textbox.tag_config(level.lower(), foreground=config["color"])
        
        self.output_text._textbox.tag_config("dim", foreground=DIM_COLOR)
        self.output_text._textbox.tag_config("cyan", foreground=ACCENT_COLOR)
        self.output_text._textbox.tag_config("default", foreground=TEXT_COLOR)
        self.output_text._textbox.tag_config("search_highlight", background="#7d5800", foreground="#ffffff")
        self.output_text._textbox.tag_config("search_current", background="#e8a317", foreground="#000000")

    # ─── Search Logic ─────────────────────────────────────

    def perform_search(self):
        """Highlight all matches in the output area."""
        # Access the internal tkinter Text widget
        tw = self.output_text._textbox
        tw.tag_remove("search_highlight", "1.0", "end")
        tw.tag_remove("search_current", "1.0", "end")
        self.search_matches = []
        self.current_match_index = -1

        query = self.search_entry.get().strip()
        if not query:
            self.search_count_label.configure(text="")
            return

        # Case-insensitive search
        start = "1.0"
        while True:
            pos = tw.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(query)}c"
            tw.tag_add("search_highlight", pos, end_pos)
            self.search_matches.append(pos)
            start = end_pos

        total = len(self.search_matches)
        if total > 0:
            self.current_match_index = 0
            self._highlight_current_match()
            self.search_count_label.configure(text=f"1 of {total}")
        else:
            self.search_count_label.configure(text="No matches")

    def navigate_search(self, direction):
        """Jump to the next (+1) or previous (-1) match."""
        if not self.search_matches:
            return
        tw = self.output_text._textbox
        # Remove current highlight
        tw.tag_remove("search_current", "1.0", "end")
        self.current_match_index = (self.current_match_index + direction) % len(self.search_matches)
        self._highlight_current_match()
        total = len(self.search_matches)
        self.search_count_label.configure(text=f"{self.current_match_index + 1} of {total}")

    def _highlight_current_match(self):
        """Apply the 'current match' highlight and scroll to it."""
        if self.current_match_index < 0 or self.current_match_index >= len(self.search_matches):
            return
        tw = self.output_text._textbox
        pos = self.search_matches[self.current_match_index]
        query = self.search_entry.get().strip()
        end_pos = f"{pos}+{len(query)}c"
        tw.tag_add("search_current", pos, end_pos)
        tw.tag_raise("search_current")
        tw.see(pos)

    def clear_search(self):
        """Clear search highlights and reset state."""
        self.search_entry.delete(0, "end")
        tw = self.output_text._textbox
        tw.tag_remove("search_highlight", "1.0", "end")
        tw.tag_remove("search_current", "1.0", "end")
        self.search_matches = []
        self.current_match_index = -1
        self.search_count_label.configure(text="")

    # ─── Display Logic ────────────────────────────────────

    def toggle_filter(self, level):
        """Toggle a log level filter on/off."""
        self.active_filters[level] = not self.active_filters[level]
        btn = self.filter_btns[level]
        color = LOG_LEVEL_MAP[level]["color"]
        if self.active_filters[level]:
            btn.configure(fg_color="#1a1a1a", text_color=color, border_color=color)
        else:
            btn.configure(fg_color="transparent", text_color=DIM_COLOR, border_color=DIM_COLOR)
        self.refresh_output()

    def refresh_output(self):

        if not self.active_session_id or self.active_session_id not in self.sessions:
            return
        session = self.sessions[self.active_session_id]
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        for log in session.logs:
            if not self.active_filters.get(log["level"], True):
                continue
                
            prefix = f"[{log['timestamp']}] "

            if self.show_thread_prefix:
                prefix += f"[{log.get('thread', 'Main')}/{log['level']}] "
            
            self.output_text.insert("end", prefix, "dim")
            self.output_text.insert("end", log["message"] + "\n", log["tag"])
        self.output_text.configure(state="disabled")
        self.output_text.see("end")
        self.log_count = len(session.logs)
        self.status_label.configure(text=f"☰ {self.log_count} LINES")



    def write_log(self, message, force_tag=None, session_id=None):
        sid = session_id or self.active_session_id
        if not sid or sid not in self.sessions:
            return
        level = "INFO"
        tag = "default"
        upper_msg = message.upper()
        for lvl, config in LOG_LEVEL_MAP.items():
            if any(kw in upper_msg for kw in config["keywords"]):
                level = lvl
                tag = lvl.lower()
                break
        if force_tag:
            tag = force_tag
            if force_tag == "dim": level = "TRACE"
            elif force_tag == "cyan": level = "INFO"
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        thread_name = threading.current_thread().name
        if thread_name == "MainThread": thread_name = "Main"
        
        log_entry = {
            "timestamp": timestamp, 
            "level": level, 
            "thread": thread_name,
            "message": message, 
            "tag": tag
        }
        self.sessions[sid].logs.append(log_entry)
        
        if sid == self.active_session_id:
            if self.active_filters.get(level, True):
                prefix = f"[{timestamp}] "
                if self.show_thread_prefix:
                    prefix += f"[{thread_name}/{level}] "

                self.output_text.configure(state="normal")
                self.output_text.insert("end", prefix, "dim")
                self.output_text.insert("end", message + "\n", tag)
                self.output_text.configure(state="disabled")
                self.output_text.see("end")

            self.log_count = len(self.sessions[sid].logs)
            self.status_label.configure(text=f"☰ {self.log_count} LINES")


    # ─── Session Management ────────────────────────────────

    def open_new_session_dialog(self):
        NewSessionDialog(self, self.create_session)

    def create_session(self, name, is_admin, shell_type="CMD", bash_path=None, ps_path=None):
        session_id = f"sess_{datetime.now().timestamp()}"
        new_session = Session(session_id, name, is_admin, self.cwd, shell_type, bash_path, ps_path)
        self.sessions[session_id] = new_session
        self.switch_to_session(session_id)
        self.write_log(f"━━━ SESSION STARTED: {name} {'(ADMIN)' if is_admin else ''} ━━━", "cyan")
        self.write_log(f"Working directory: {self.cwd}", "dim")
        self.write_log("Terminal ready.", "INFO")
        self.render_instances()

    def switch_to_session(self, session_id):
        self.active_session_id = session_id
        session = self.sessions[session_id]
        self.cwd = session.cwd
        self.active_session_label.configure(text=f"● {session.name}", text_color=session.color)
        self.welcome_frame.grid_remove()
        self.output_text.grid(row=0, column=0, sticky="nsew")
        self.clear_search()
        self.refresh_output()
        self.render_instances()

    def render_instances(self):
        for widget in self.session_scroll.winfo_children(): widget.destroy()
        count = len(self.sessions)
        self.session_count_badge.configure(text=str(count), fg_color=ACCENT_COLOR if count > 0 else BORDER_COLOR, text_color=BG_COLOR if count > 0 else DIM_COLOR)
        groups: dict[str, list[Session]] = {}
        for sess in self.sessions.values():
            g = sess.group or "Default"
            if g not in groups: groups[g] = []
            groups[g].append(sess)
        for idx, (group_name, sess_list) in enumerate(sorted(groups.items())):
            if len(groups) > 1 or group_name != "Default":
                if idx > 0: ctk.CTkFrame(self.session_scroll, height=1, fg_color=BORDER_COLOR).pack(fill="x", padx=8, pady=(8, 4))
                group_header = ctk.CTkFrame(self.session_scroll, fg_color="transparent")
                group_header.pack(fill="x", padx=8, pady=(8, 4))
                ctk.CTkLabel(group_header, text="▸", font=("Roboto", 12, "bold"), text_color=ACCENT_COLOR).pack(side="left")
                ctk.CTkLabel(group_header, text=f" {group_name.upper()}", font=("Roboto", 12, "bold"), text_color=DIM_COLOR).pack(side="left")
                ctk.CTkLabel(group_header, text=f"({len(sess_list)})", font=("Roboto", 12), text_color=BORDER_COLOR).pack(side="left", padx=(5, 0))




            for sess in sess_list:
                is_active = sess.id == self.active_session_id
                card = SessionCard(self.session_scroll, sess, is_active, self.switch_to_session, self.show_context_menu)
                card.pack(fill="x", padx=4, pady=3)

    def show_context_menu(self, event, session_id):
        self.menu_session_target = session_id
        self.context_menu.post(event.x_root, event.y_root)

    def menu_rename(self):
        s_id = self.menu_session_target
        if not s_id or s_id not in self.sessions: return
        new_name = simpledialog.askstring("Rename Session", "Enter new name:", initialvalue=self.sessions[s_id].name)
        if new_name:
            self.sessions[s_id].name = new_name
            if s_id == self.active_session_id: self.active_session_label.configure(text=f"● {new_name}")
            self.render_instances()

    def menu_set_color(self):
        s_id = self.menu_session_target
        if not s_id or s_id not in self.sessions: return
        _, color = colorchooser.askcolor(initialcolor=self.sessions[s_id].color)
        if color:
            self.sessions[s_id].color = color
            if s_id == self.active_session_id: self.active_session_label.configure(text_color=color)
            self.render_instances()

    def menu_group(self):
        s_id = self.menu_session_target
        if not s_id or s_id not in self.sessions: return
        new_group = simpledialog.askstring("Group Session", "Enter group name:", initialvalue=self.sessions[s_id].group)
        if new_group:
            self.sessions[s_id].group = new_group
            self.render_instances()

    def menu_duplicate(self):
        s_id = self.menu_session_target
        if not s_id or s_id not in self.sessions: return
        old = self.sessions[s_id]
        session_id = f"sess_{datetime.now().timestamp()}"
        new_session = Session(session_id, f"{old.name} (Copy)", old.is_admin, self.cwd, old.shell_type, old.bash_path, old.ps_path)
        new_session.logs = [log.copy() for log in old.logs]
        new_session.log_count = old.log_count
        new_session.group = old.group
        new_session.color = old.color
        self.sessions[session_id] = new_session
        self.switch_to_session(session_id)
        self.render_instances()

    def menu_close(self):
        s_id = self.menu_session_target
        if not s_id or s_id not in self.sessions: return
        del self.sessions[s_id]
        if not self.sessions:
            self.active_session_id = None
            self.output_text.grid_remove()
            self.welcome_frame.grid()
            self.active_session_label.configure(text="")
        elif s_id == self.active_session_id:
            next_id = list(self.sessions.keys())[0]
            self.switch_to_session(next_id)
        self.render_instances()

    def update_uptime(self):
        if self.sessions: self.render_instances()
        self.after(30000, self.update_uptime)

    def on_enter(self, event):
        if not self.active_session_id:
            self.open_new_session_dialog()
            return
        cmd = self.command_entry.get().strip()
        if not cmd: return
        self.command_entry.delete(0, "end")
        self.write_log(f"❯ {cmd}", "cyan")
        parts = cmd.split()
        base = parts[0].lower()
        if base == "clear":
            self.clear_logs()
            return
        elif base == "exit":
            self.menu_session_target = self.active_session_id
            self.menu_close()
            return
        elif base == "cd":
            target = " ".join(parts[1:]) if len(parts) > 1 else os.path.expanduser("~")
            try:
                os.chdir(target)
                self.cwd = os.getcwd()
                if self.active_session_id: self.sessions[self.active_session_id].cwd = self.cwd
                self.write_log(f"Changed directory to {self.cwd}", "dim")
                self.render_instances()
            except Exception as e: self.write_log(f"cd error: {e}", "red")
            return
        threading.Thread(target=self.run_process, args=(cmd, self.active_session_id), daemon=True).start()

    def run_process(self, cmd, session_id):
        session = self.sessions.get(session_id)
        if not session: return
        try:
            if session.shell_type == "Git Bash" and session.bash_path:
                popen_args = [session.bash_path, "--login", "-i", "-c", cmd]
                process = subprocess.Popen(popen_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=session.cwd)
            elif session.shell_type == "PowerShell":
                ps_exe = session.ps_path or "powershell.exe"
                popen_args = [ps_exe, "-Command", cmd]
                process = subprocess.Popen(popen_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=session.cwd)
            else:
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=session.cwd)
                
            stdout, stderr = process.communicate()
            if stdout:
                for line in stdout.splitlines(): self.write_log(f"  ├── {line}", session_id=session_id)
            if stderr:
                for line in stderr.splitlines(): self.write_log(f"  ├── {line}", "red", session_id=session_id)
            if not stdout and not stderr: self.write_log("  └── (no output)", "dim", session_id=session_id)
        except Exception as e: self.write_log(f"Execution Error: {e}", "red", session_id=session_id)

    def clear_logs(self):
        ConfirmDialog(self, "Clear Logs", "Are you sure you want to clear the logs for this session?", self._perform_clear_logs)

    def _perform_clear_logs(self):
        if self.active_session_id and self.active_session_id in self.sessions: self.sessions[self.active_session_id].logs = []
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.log_count = 0
        self.status_label.configure(text="☰ 0 LINES")

if __name__ == "__main__":
    app = Ariterminal()
    app.mainloop()
