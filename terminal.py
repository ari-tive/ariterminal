import customtkinter as ctk
import os
import subprocess
from datetime import datetime
import threading
from typing import Optional

# Color Constants
BG_COLOR = "#0d1117"
SURFACE_COLOR = "#161b22"
ACCENT_COLOR = "#00bcd4"
TEXT_COLOR = "#c9d1d9"
GREEN_COLOR = "#238636"
RED_COLOR = "#da3633"
YELLOW_COLOR = "#d29922"

class NewSessionDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_create):
        super().__init__(parent)
        self.title("New Session")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)  # Keep it on top of parent
        self.grab_set()         # Modal dialog
        
        self.on_create = on_create
        self.configure(fg_color=SURFACE_COLOR)

        # Centering in parent
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        self.geometry(f"+{parent_x + (parent_w // 2) - 200}+{parent_y + (parent_h // 2) - 150}")

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="CREATE NEW SESSION", font=("Segoe UI", 16, "bold"), text_color=ACCENT_COLOR).grid(row=0, column=0, pady=(20, 10))

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Session Name", width=300, fg_color=BG_COLOR, border_color="#30363d")
        self.name_entry.insert(0, "Session 1")
        self.name_entry.grid(row=1, column=0, pady=10)

        self.admin_var = ctk.BooleanVar(value=False)
        self.admin_check = ctk.CTkCheckBox(self, text="Run as Administrator", variable=self.admin_var, 
                                          fg_color=ACCENT_COLOR, hover_color="#008ba3", border_color="#30363d")
        self.admin_check.grid(row=2, column=0, pady=10)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=3, column=0, pady=20)

        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="CANCEL", width=100, fg_color="transparent", 
                                        border_width=1, border_color=RED_COLOR, text_color=RED_COLOR, command=self.destroy)
        self.cancel_btn.pack(side="left", padx=10)

        self.create_btn = ctk.CTkButton(self.btn_frame, text="CREATE SESSION", width=150, fg_color=ACCENT_COLOR, 
                                        hover_color="#008ba3", text_color=BG_COLOR, font=("Segoe UI", 12, "bold"),
                                        command=self._on_confirm)
        self.create_btn.pack(side="left", padx=10)

    def _on_confirm(self):
        name = self.name_entry.get().strip() or "Session 1"
        is_admin = self.admin_var.get()
        self.on_create(name, is_admin)
        self.destroy()

class Ariterminal(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ariterminal")
        self.geometry("1100x700")
        self.configure(fg_color=BG_COLOR)

        self.cwd = os.getcwd()
        self.history = []
        self.log_count = 0
        self.start_time = datetime.now()
        self.active_session = None

        # Set appearance
        ctk.set_appearance_mode("dark")
        
        self.setup_ui()
        self.update_uptime()

    def setup_ui(self):
        # Configure grid for root
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- TOP BAR ---
        self.top_bar = ctk.CTkFrame(self, height=50, fg_color=SURFACE_COLOR, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.top_bar.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(self.top_bar, text=">_ ARITERMINAL", font=("Segoe UI", 16, "bold"), text_color=ACCENT_COLOR)
        self.title_label.grid(row=0, column=0, padx=20, pady=10)

        self.search_entry = ctk.CTkEntry(self.top_bar, placeholder_text="🔍 Search logs...", width=300, 
                                        fg_color=BG_COLOR, border_color="#30363d")
        self.search_entry.grid(row=0, column=1, padx=10, pady=10)

        self.filter_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.filter_frame.grid(row=0, column=2, padx=10)

        filters = [("ERROR", RED_COLOR), ("WARN", YELLOW_COLOR), ("INFO", ACCENT_COLOR), ("DEBUG", "#bc8cff"), ("TRACE", "#8b949e")]
        for i, (name, color) in enumerate(filters):
            btn = ctk.CTkButton(self.filter_frame, text=name, width=60, height=24, fg_color="transparent", 
                                border_width=1, border_color=color, text_color=color, font=("Segoe UI", 10, "bold"))
            btn.grid(row=0, column=i, padx=2)

        self.settings_btn = ctk.CTkButton(self.top_bar, text="⚙", width=30, height=30, fg_color="transparent", text_color="#8b949e")
        self.settings_btn.grid(row=0, column=3, padx=20)

        # --- MAIN AREA ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=8)
        self.main_container.grid_columnconfigure(1, weight=2)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Output Area Container
        self.output_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.output_container.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.output_container.grid_columnconfigure(0, weight=1)
        self.output_container.grid_rowconfigure(0, weight=1)

        # Terminal Textbox (hidden initially)
        self.output_text = ctk.CTkTextbox(self.output_container, font=("Consolas", 12), fg_color=BG_COLOR, 
                                         text_color=TEXT_COLOR, border_width=1, border_color="#30363d")
        self.output_text.configure(state="disabled")

        # Welcome Screen
        self.welcome_frame = ctk.CTkFrame(self.output_container, fg_color=BG_COLOR, border_width=1, border_color="#30363d")
        self.welcome_frame.grid(row=0, column=0, sticky="nsew")
        
        self.welcome_inner = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        self.welcome_inner.place(relx=0.5, rely=0.5, anchor="center")
        
        self.welcome_label = ctk.CTkLabel(self.welcome_inner, text="No active sessions", font=("Segoe UI", 24, "bold"), text_color=TEXT_COLOR)
        self.welcome_label.pack(pady=(0, 5))
        
        self.welcome_subtext = ctk.CTkLabel(self.welcome_inner, text="Create a new session to get started", font=("Segoe UI", 12), text_color="#8b949e")
        self.welcome_subtext.pack(pady=(0, 20))
        
        self.new_session_btn = ctk.CTkButton(self.welcome_inner, text="+ New Session", fg_color=ACCENT_COLOR, hover_color="#008ba3",
                                             text_color=BG_COLOR, font=("Segoe UI", 14, "bold"), height=40,
                                             command=self.open_new_session_dialog)
        self.new_session_btn.pack()

        # Right Instances Panel
        self.instances_panel = ctk.CTkFrame(self.main_container, fg_color=SURFACE_COLOR, border_width=1, border_color=ACCENT_COLOR)
        self.instances_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        self.inst_title = ctk.CTkLabel(self.instances_panel, text="🖥 Instances", font=("Segoe UI", 14, "bold"), text_color=ACCENT_COLOR)
        self.inst_title.pack(pady=15, padx=10, anchor="w")

        # Session Card
        self.session_card = ctk.CTkFrame(self.instances_panel, fg_color=BG_COLOR, border_width=1, border_color="#30363d")
        self.session_card.pack(fill="x", padx=10, pady=5)
        
        self.user_label = ctk.CTkLabel(self.session_card, text=f"👤 {os.getlogin()}", font=("Segoe UI", 11), text_color="#8b949e")
        self.user_label.pack(pady=(10, 2), padx=10, anchor="w")
        
        self.dir_label = ctk.CTkLabel(self.session_card, text="📁 " + self._get_short_cwd(), font=("Segoe UI", 11), text_color="#8b949e")
        self.dir_label.pack(pady=2, padx=10, anchor="w")

        self.uptime_label = ctk.CTkLabel(self.session_card, text="⏱ 00:00:00", font=("Segoe UI", 11), text_color="#8b949e")
        self.uptime_label.pack(pady=(2, 10), padx=10, anchor="w")

        self.start_btn = ctk.CTkButton(self.instances_panel, text="▶ START SESSION", fg_color=GREEN_COLOR, hover_color="#2ea043",
                                      font=("Segoe UI", 12, "bold"), height=35, command=self.open_new_session_dialog)
        self.start_btn.pack(side="bottom", fill="x", padx=15, pady=20)

        # --- BOTTOM BAR ---
        self.bottom_bar = ctk.CTkFrame(self, height=40, fg_color=SURFACE_COLOR, corner_radius=0)
        self.bottom_bar.grid(row=2, column=0, sticky="ew")
        self.bottom_bar.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(self.bottom_bar, text="☰ 0 LINES", width=100, text_color="#8b949e", font=("Segoe UI", 10))
        self.status_label.grid(row=0, column=0, padx=10)

        self.follow_btn = ctk.CTkButton(self.bottom_bar, text="⬇ FOLLOWING", width=100, height=20, fg_color="transparent", 
                                       text_color=ACCENT_COLOR, font=("Segoe UI", 10, "bold"))
        self.follow_btn.grid(row=0, column=1, sticky="w")

        # Command Input Area
        self.input_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        self.input_frame.grid(row=0, column=2, sticky="ew", padx=10)
        
        self.prompt_label = ctk.CTkLabel(self.input_frame, text="❯", text_color=ACCENT_COLOR, font=("Consolas", 14, "bold"))
        self.prompt_label.pack(side="left", padx=(5, 0))
        
        self.command_entry = ctk.CTkEntry(self.input_frame, fg_color="transparent", border_width=0, 
                                         text_color=TEXT_COLOR, font=("Consolas", 12), placeholder_text="Enter command...")
        self.command_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.command_entry.bind("<Return>", self.on_enter)

        self.clear_btn = ctk.CTkButton(self.bottom_bar, text="🗑 CLEAR", width=80, height=24, fg_color="transparent", 
                                       text_color="#8b949e", hover_color="#30363d", command=self.clear_logs)
        self.clear_btn.grid(row=0, column=3, padx=5)

        self.upload_btn = ctk.CTkButton(self.bottom_bar, text="📤 UPLOAD", width=80, height=24, fg_color="transparent", 
                                        text_color="#8b949e", hover_color="#30363d")
        self.upload_btn.grid(row=0, column=4, padx=10)

        # Log styles
        self.output_text.tag_config("cyan", foreground=ACCENT_COLOR)
        self.output_text.tag_config("dim", foreground="#8b949e")
        self.output_text.tag_config("red", foreground=RED_COLOR)

    def _get_short_cwd(self):
        home = os.path.expanduser("~")
        cwd = self.cwd
        return cwd.replace(home, "~") if cwd.startswith(home) else cwd

    def update_uptime(self):
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.uptime_label.configure(text=f"⏱ {hours:02}:{minutes:02}:{seconds:02}")
        self.after(1000, self.update_uptime)

    def open_new_session_dialog(self):
        NewSessionDialog(self, self.create_session)

    def create_session(self, name, is_admin):
        self.active_session = {"name": name, "admin": is_admin}
        
        # UI Transitions
        self.welcome_frame.grid_remove()
        self.output_text.grid(row=0, column=0, sticky="nsew")
        
        self.write_log(f"--- NEW SESSION: {name} {'(ADMIN)' if is_admin else ''} ---", "cyan")
        self.write_log("Initializing desktop shell environment...", "dim")
        self.write_log("- Ariterminal system READY", "dim")

    def write_log(self, message, tag=None):
        if not self.active_session:
            return

        self.output_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] "
        self.output_text.insert("end", prefix, "dim")
        self.output_text.insert("end", message + "\n", tag)
        self.output_text.configure(state="disabled")
        self.output_text.see("end")
        
        self.log_count += 1
        self.status_label.configure(text=f"☰ {self.log_count} LINES")

    def on_enter(self, event):
        if not self.active_session:
            self.open_new_session_dialog()
            return

        cmd = self.command_entry.get().strip()
        if not cmd:
            return
        
        self.command_entry.delete(0, "end")
        self.write_log(f"❯ {cmd}", "cyan")
        
        # Internal commands
        parts = cmd.split()
        base = parts[0].lower()
        
        if base == "clear":
            self.clear_logs()
            return
        elif base == "help":
            self.write_log("Available: help, clear, exit, cd [dir], or any system command.")
            return
        elif base == "exit":
            self.quit()
            return
        elif base == "cd":
            target = " ".join(parts[1:]) if len(parts) > 1 else os.path.expanduser("~")
            try:
                os.chdir(target)
                self.cwd = os.getcwd()
                self.dir_label.configure(text="📁 " + self._get_short_cwd())
                self.write_log(f"Changed directory to {self.cwd}", "dim")
            except Exception as e:
                self.write_log(f"cd error: {e}", "red")
            return

        # Run in thread to not block UI
        threading.Thread(target=self.run_process, args=(cmd,), daemon=True).start()

    def run_process(self, cmd):
        try:
            # Handle admin if needed (though on Windows this is complex from inside Python without elevation)
            # For now, we just pass the command
            process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                text=True, cwd=self.cwd
            )
            stdout, stderr = process.communicate()
            
            if stdout:
                for line in stdout.splitlines():
                    self.write_log(f"  |-- {line}")
            if stderr:
                for line in stderr.splitlines():
                    self.write_log(f"  |-- {line}", "red")
            if not stdout and not stderr:
                self.write_log("  \\-- (no output)", "dim")
                
        except Exception as e:
            self.write_log(f"Execution Error: {e}", "red")

    def clear_logs(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.log_count = 0
        self.status_label.configure(text=f"☰ 0 LINES")

if __name__ == "__main__":
    app = Ariterminal()
    app.mainloop()
   app = Ariterminal()
    app.mainloop()