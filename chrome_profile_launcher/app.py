import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from tkinter import messagebox

from .config import (
    load_config, save_config, AppConfig, ProfileConfig,
    CONFIG_DIR, CHROME_DATA_DIR
)
from .launcher import (
    launch_all, force_close, tile_chrome_windows,
    get_current_chrome_windows
)

TAG_COLORS = {
    "Trading": "#FF6B35",
    "Social": "#4361EE",
    "Work": "#2EC4B6",
    "Banking": "#E71D36",
    "Shopping": "#FF9F1C",
    "Entertainment": "#9D4EDD",
    "default": "#6C757D",
}
PROFILE_NAMES = [f"Profile {i}" for i in range(1, 13)]


def _tag_color(tag: str) -> str:
    return TAG_COLORS.get(tag, TAG_COLORS["default"])


class ProfileRow(ctk.CTkFrame):
    def __init__(self, parent, index: int, config: ProfileConfig,
                 on_toggle_advanced=None, on_tag_click=None, **kwargs):
        super().__init__(parent, corner_radius=8, **kwargs)
        self.index = index
        self.config = config
        self.on_toggle_advanced = on_toggle_advanced
        self.on_tag_click = on_tag_click
        self._advanced_shown = False
        self._advanced_frame: Optional[ctk.CTkFrame] = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(2, weight=1)

        self.check_var = ctk.BooleanVar(value=self.config.enabled)
        self.checkbox = ctk.CTkCheckBox(self, text="", variable=self.check_var,
                                         width=20, corner_radius=4)
        self.checkbox.grid(row=0, column=0, padx=(8, 4), pady=6, sticky="w")

        self.name_label = ctk.CTkLabel(self, text=f"Profile {self.index}",
                                        font=ctk.CTkFont(size=13, weight="bold"))
        self.name_label.grid(row=0, column=1, padx=(0, 6), pady=6, sticky="w")

        self.tag_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tag_frame.grid(row=0, column=2, padx=4, pady=6, sticky="w")
        self._render_tags()

        self.advanced_btn = ctk.CTkButton(self, text="\u2699\ufe0f", width=30, height=24,
                                           corner_radius=6, font=ctk.CTkFont(size=14),
                                           command=self._toggle_advanced)
        self.advanced_btn.grid(row=0, column=3, padx=(4, 8), pady=6, sticky="e")

    def _render_tags(self):
        for w in self.tag_frame.winfo_children():
            w.destroy()
        for tag in self.config.tags:
            lbl = ctk.CTkLabel(self.tag_frame, text=tag, corner_radius=4,
                                fg_color=_tag_color(tag),
                                text_color="white",
                                font=ctk.CTkFont(size=10),
                                padx=6, pady=1)
            lbl.pack(side="left", padx=2)

        add_btn = ctk.CTkButton(self.tag_frame, text="+", width=22, height=18,
                                 corner_radius=4, font=ctk.CTkFont(size=12),
                                 command=self._add_tag)
        add_btn.pack(side="left", padx=2)

    def _add_tag(self):
        dialog = ctk.CTkInputDialog(text=f"Add tag for Profile {self.index}:",
                                     title="Add Tag")
        tag = dialog.get_input()
        if tag and tag.strip():
            tag = tag.strip()
            if tag not in self.config.tags:
                self.config.tags.append(tag)
                self._render_tags()

    def _toggle_advanced(self):
        self._advanced_shown = not self._advanced_shown
        if self._advanced_shown:
            if not self._advanced_frame:
                self._build_advanced()
            self._advanced_frame.grid(row=1, column=0, columnspan=4,
                                       padx=8, pady=(0, 6), sticky="ew")
        else:
            if self._advanced_frame:
                self._advanced_frame.grid_remove()

    def _build_advanced(self):
        self._advanced_frame = ctk.CTkFrame(self, fg_color=("#E8E8E8", "#2A2A2A"),
                                              corner_radius=6)
        self._advanced_frame.grid_columnconfigure((1, 3), weight=1)

        self.proxy_var = ctk.BooleanVar(value=self.config.proxy.enabled)
        proxy_cb = ctk.CTkCheckBox(self._advanced_frame, text="Proxy",
                                    variable=self.proxy_var, corner_radius=4)
        proxy_cb.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")

        lbl = ctk.CTkLabel(self._advanced_frame, text="IP:Port",
                            font=ctk.CTkFont(size=11))
        lbl.grid(row=0, column=1, padx=(0, 2), pady=4, sticky="w")
        self.proxy_ip_entry = ctk.CTkEntry(self._advanced_frame,
                                            placeholder_text="192.168.1.1",
                                            width=120, corner_radius=6)
        self.proxy_ip_entry.insert(0, self.config.proxy.ip)
        self.proxy_ip_entry.grid(row=0, column=2, padx=2, pady=4, sticky="w")

        self.proxy_port_entry = ctk.CTkEntry(self._advanced_frame,
                                              placeholder_text="8080",
                                              width=60, corner_radius=6)
        self.proxy_port_entry.insert(0, self.config.proxy.port)
        self.proxy_port_entry.grid(row=0, column=3, padx=2, pady=4, sticky="w")

        u_lbl = ctk.CTkLabel(self._advanced_frame, text="User",
                              font=ctk.CTkFont(size=11))
        u_lbl.grid(row=1, column=0, padx=(6, 2), pady=4, sticky="w")
        self.proxy_user_entry = ctk.CTkEntry(self._advanced_frame,
                                              placeholder_text="username",
                                              width=120, corner_radius=6)
        self.proxy_user_entry.insert(0, self.config.proxy.username)
        self.proxy_user_entry.grid(row=1, column=1, padx=2, pady=4, sticky="ew")

        p_lbl = ctk.CTkLabel(self._advanced_frame, text="Pass",
                              font=ctk.CTkFont(size=11))
        p_lbl.grid(row=1, column=2, padx=(6, 2), pady=4, sticky="w")
        self.proxy_pass_entry = ctk.CTkEntry(self._advanced_frame,
                                              placeholder_text="password",
                                              width=100, corner_radius=6,
                                              show="*")
        self.proxy_pass_entry.insert(0, self.config.proxy.password)
        self.proxy_pass_entry.grid(row=1, column=3, padx=2, pady=4, sticky="w")

    def save_state(self):
        self.config.enabled = self.check_var.get()
        if self._advanced_frame and self._advanced_shown:
            self.config.proxy.enabled = self.proxy_var.get()
            self.config.proxy.ip = self.proxy_ip_entry.get().strip()
            self.config.proxy.port = self.proxy_port_entry.get().strip()
            self.config.proxy.username = self.proxy_user_entry.get().strip()
            self.config.proxy.password = self.proxy_pass_entry.get().strip()


class LogConsole(ctk.CTkTextbox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, corner_radius=8, **kwargs)
        self.configure(state="disabled")

    def write(self, message: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        emoji = {"info": "\u2139\ufe0f", "success": "\u2705",
                 "error": "\u274c", "warning": "\u26a0\ufe0f"}
        prefix = emoji.get(level, "\u2139\ufe0f")
        line = f"[{ts}] {prefix} {message}\n"
        self.configure(state="normal")
        self.insert("end", line)
        self.see("end")
        self.configure(state="disabled")


class ProfileLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chrome Profile Launcher")
        self.geometry("800x820")
        self.resizable(False, False)

        self.config: AppConfig = load_config()
        self.profile_rows: list[ProfileRow] = []
        self._before_windows = []
        self._launching = False

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._repopulate_rows()

    # ─── UI BUILD ────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Title
        title = ctk.CTkLabel(self, text="Chrome Profile Launcher",
                              font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, pady=(16, 4), padx=20, sticky="n")

        # ─── Search + Tags ───
        top_bar = ctk.CTkFrame(self, corner_radius=10)
        top_bar.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)

        search_lbl = ctk.CTkLabel(top_bar, text="\U0001f50d", font=ctk.CTkFont(size=16))
        search_lbl.grid(row=0, column=0, padx=(10, 4), pady=8, sticky="w")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_rows())
        search_entry = ctk.CTkEntry(top_bar, placeholder_text="Search profiles...",
                                     textvariable=self.search_var, corner_radius=8)
        search_entry.grid(row=0, column=1, padx=4, pady=8, sticky="ew")

        tag_lbl = ctk.CTkLabel(top_bar, text="Tags:", font=ctk.CTkFont(size=12))
        tag_lbl.grid(row=0, column=2, padx=(8, 2), pady=8, sticky="w")

        self.tag_filter_var = ctk.StringVar(value="All")

        def tag_filter_changed(*_):
            self._filter_rows()

        tag_menu = ctk.CTkOptionMenu(top_bar, values=["All"] + self.config.tags_pool,
                                      variable=self.tag_filter_var, width=100,
                                      corner_radius=8, command=lambda _: self._filter_rows())
        tag_menu.grid(row=0, column=3, padx=(0, 8), pady=8, sticky="w")

        # ─── Profiles (scrollable) ───
        self.profiles_container = ctk.CTkScrollableFrame(self, corner_radius=10,
                                                          label_text="Profiles",
                                                          label_font=ctk.CTkFont(size=14, weight="bold"))
        self.profiles_container.grid(row=2, column=0, padx=20, pady=(0, 8), sticky="nsew")

        # Select / Deselect
        sel_frame = ctk.CTkFrame(self, fg_color="transparent")
        sel_frame.grid(row=3, column=0, padx=20, pady=(0, 4), sticky="w")
        ctk.CTkButton(sel_frame, text="Select All", width=90, corner_radius=8,
                       command=self._select_all).pack(side="left", padx=(0, 6))
        ctk.CTkButton(sel_frame, text="Deselect All", width=90, corner_radius=8,
                       command=self._deselect_all).pack(side="left")

        # ─── URLs ───
        urls_frame = ctk.CTkFrame(self, corner_radius=10)
        urls_frame.grid(row=4, column=0, padx=20, pady=(0, 6), sticky="ew")
        urls_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(urls_frame, text="URLs",
                      font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(8, 4), sticky="w")

        self.url_entries = []
        defaults = self.config.urls
        for i in range(5):
            lbl = ctk.CTkLabel(urls_frame, text=f"{i + 1}.", width=20, anchor="e",
                                font=ctk.CTkFont(size=12))
            lbl.grid(row=i + 1, column=0, padx=(10, 2), pady=3, sticky="e")
            entry = ctk.CTkEntry(urls_frame, placeholder_text=f"URL {i + 1}...",
                                  corner_radius=6)
            if i < len(defaults):
                entry.insert(0, defaults[i])
            entry.grid(row=i + 1, column=1, padx=(0, 10), pady=3, sticky="ew")
            self.url_entries.append(entry)

        # ─── Settings row ───
        settings_frame = ctk.CTkFrame(self, corner_radius=10)
        settings_frame.grid(row=5, column=0, padx=20, pady=(0, 6), sticky="ew")
        settings_frame.grid_columnconfigure(3, weight=1)

        self.human_var = ctk.BooleanVar(value=self.config.human_like_delay)
        human_cb = ctk.CTkCheckBox(settings_frame, text="Human-Like Launch",
                                    variable=self.human_var, corner_radius=4)
        human_cb.grid(row=0, column=0, padx=(10, 4), pady=10, sticky="w")

        ctk.CTkLabel(settings_frame, text="Delay:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=1, padx=(4, 2), pady=10, sticky="w")

        self.delay_min_var = ctk.StringVar(value=str(self.config.delay_min))
        delay_min_entry = ctk.CTkEntry(settings_frame, textvariable=self.delay_min_var,
                                        width=40, corner_radius=6)
        delay_min_entry.grid(row=0, column=2, padx=2, pady=10, sticky="w")

        ctk.CTkLabel(settings_frame, text="-", font=ctk.CTkFont(size=14)).grid(
            row=0, column=3, padx=0, pady=10, sticky="w")

        self.delay_max_var = ctk.StringVar(value=str(self.config.delay_max))
        delay_max_entry = ctk.CTkEntry(settings_frame, textvariable=self.delay_max_var,
                                        width=40, corner_radius=6)
        delay_max_entry.grid(row=0, column=4, padx=2, pady=10, sticky="w")

        ctk.CTkLabel(settings_frame, text="sec", font=ctk.CTkFont(size=12)).grid(
            row=0, column=5, padx=(0, 10), pady=10, sticky="w")

        # ─── Action buttons ───
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=6, column=0, padx=20, pady=(0, 4), sticky="ew")
        action_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(action_frame, text="\U0001f680 Launch", fg_color="#2B7A4B",
                       hover_color="#1F5C38", height=40, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._launch_profiles).grid(
            row=0, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkButton(action_frame, text="\U0001f6d1 Force Close", fg_color="#B32424",
                       hover_color="#8A1B1B", height=40, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._force_close).grid(
            row=0, column=1, padx=4, sticky="ew")

        ctk.CTkButton(action_frame, text="\U0001f9f0 Tile Windows", fg_color="#3A3A5C",
                       hover_color="#2A2A4C", height=40, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._tile_windows).grid(
            row=0, column=2, padx=(4, 0), sticky="ew")

        # ─── Progress ───
        self.progress_bar = ctk.CTkProgressBar(self, corner_radius=6)
        self.progress_bar.grid(row=7, column=0, padx=20, pady=(4, 2), sticky="ew")
        self.progress_bar.set(0)

        # ─── Log console ───
        self.log_console = LogConsole(self, height=110, corner_radius=8)
        self.log_console.grid(row=8, column=0, padx=20, pady=(2, 2), sticky="ew")

        credit = ctk.CTkLabel(self, text="Developed by ImranDev3  |  github.com/ImranDev3",
                               font=ctk.CTkFont(size=11), text_color="#888888")
        credit.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="s")

    # ─── PROFILE ROWS ────────────────────────────────────────

    def _repopulate_rows(self, filter_text: str = "", filter_tag: str = ""):
        for row in self.profile_rows:
            row.destroy()
        self.profile_rows.clear()

        for i in range(12):
            name = f"Profile {i + 1}"
            if filter_text and filter_text.lower() not in name.lower():
                tags_text = " ".join(self.config.profiles[i].tags).lower()
                if filter_text.lower() not in tags_text:
                    continue
            if filter_tag and filter_tag != "All":
                if filter_tag not in self.config.profiles[i].tags:
                    continue

            row = ProfileRow(self.profiles_container, i + 1, self.config.profiles[i])
            row.pack(fill="x", padx=4, pady=2)
            self.profile_rows.append(row)

    def _filter_rows(self):
        text = self.search_var.get().strip()
        tag = self.tag_filter_var.get()
        self._repopulate_rows(text, tag)

    def _select_all(self):
        for row in self.profile_rows:
            row.check_var.set(True)

    def _deselect_all(self):
        for row in self.profile_rows:
            row.check_var.set(False)

    # ─── ACTIONS ─────────────────────────────────────────────

    def _get_urls(self):
        return [e.get().strip() for e in self.url_entries if e.get().strip()]

    def _collect_profiles(self):
        result = []
        for row in self.profile_rows:
            row.save_state()
            if row.config.enabled:
                result.append((row.index, row.config))
        return result

    def _launch_profiles(self):
        if self._launching:
            return
        self._save_all()
        selected = self._collect_profiles()
        if not selected:
            self.log_console.write("No profiles selected", "warning")
            return
        urls = self._get_urls()
        if not urls:
            self.log_console.write("No URLs entered", "warning")
            return

        self._before_windows = get_current_chrome_windows()
        human = self.human_var.get()
        dmin = int(self.delay_min_var.get() or 2)
        dmax = int(self.delay_max_var.get() or 5)

        self._launching = True
        self.log_console.write(f"Launching {len(selected)} profile(s)...", "info")

        def _worker():
            launch_all(
                profiles=selected,
                urls=urls,
                user_data_dir=CHROME_DATA_DIR,
                human_like=human,
                delay_min=dmin,
                delay_max=dmax,
                progress_callback=lambda v: self.after(0, lambda: self.progress_bar.set(v)),
                log_callback=lambda m, l: self.after(0, lambda: self.log_console.write(m, l)),
            )
            self._launching = False

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _force_close(self):
        self._save_all()
        force_close(log_callback=lambda m, l: self.after(0, lambda: self.log_console.write(m, l)))

    def _tile_windows(self):
        tile_chrome_windows(self._before_windows,
                            log_callback=lambda m, l: self.after(0, lambda: self.log_console.write(m, l)))

    # ─── PERSISTENCE ─────────────────────────────────────────

    def _save_all(self):
        for row in self.profile_rows:
            row.save_state()
        self.config.human_like_delay = self.human_var.get()
        try:
            self.config.delay_min = int(self.delay_min_var.get())
            self.config.delay_max = int(self.delay_max_var.get())
        except ValueError:
            pass
        self.config.urls = self._get_urls()
        save_config(self.config)

    def _on_close(self):
        self._save_all()
        self.destroy()


def main():
    app = ProfileLauncherApp()
    app.mainloop()
