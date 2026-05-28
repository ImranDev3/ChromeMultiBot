import threading
import sys
from datetime import datetime
from typing import Optional

import customtkinter as ctk
from tkinter import messagebox

from .keyauth import KeyAuthApp
from .config import (
    load_config, save_config, AppConfig, ProfileConfig,
    load_license_key, save_license_key, clear_license_key,
    CONFIG_DIR, CHROME_DATA_DIR,
)
from .launcher import (
    launch_all, force_close, tile_chrome_windows,
    get_current_chrome_windows,
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

KEYAUTH_NAME = "ChromeMultiBot"
KEYAUTH_OWNERID = "pl7MOdBApi"
KEYAUTH_SECRET = "b03f01bbd5195f5b1ccdc08ff751d7765c09b0ff70a4492ed36471bd8ebf6b0d"
KEYAUTH_VERSION = "1.0"

TAG_COLORS = {
    "Trading": "#FF6B35",
    "Social": "#4361EE",
    "Work": "#2EC4B6",
    "Banking": "#E71D36",
    "Shopping": "#FF9F1C",
    "Entertainment": "#9D4EDD",
    "default": "#6C757D",
}
TAG_PRESETS = ["Trading", "Social", "Work", "Banking", "Shopping", "Entertainment"]


def _tag_color(tag: str) -> str:
    return TAG_COLORS.get(tag, TAG_COLORS["default"])


# ───────────────────────── LOGIN WINDOW ─────────────────────────

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ChromeMultiBot - License Activation")
        self.geometry("420x380")
        self.resizable(False, False)
        self._auth_result = None

        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self, corner_radius=14)
        frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="ChromeMultiBot",
                      font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, pady=(20, 4))
        ctk.CTkLabel(frame, text="License Activation Required",
                      font=ctk.CTkFont(size=13), text_color="#888888").grid(
            row=1, column=0, pady=(0, 20))

        ctk.CTkLabel(frame, text="License Key", font=ctk.CTkFont(size=12)).grid(
            row=2, column=0, padx=20, sticky="w")
        self.key_var = ctk.StringVar(value=load_license_key())
        self.key_entry = ctk.CTkEntry(frame, textvariable=self.key_var,
                                       placeholder_text="XXXXXX-XXXXXX-XXXXXX-XXXXXX",
                                       corner_radius=8, height=36)
        self.key_entry.grid(row=3, column=0, padx=20, pady=(4, 12), sticky="ew")

        self.remember_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame, text="Remember License Key",
                         variable=self.remember_var, corner_radius=4).grid(
            row=4, column=0, padx=20, pady=(0, 16), sticky="w")

        self.login_btn = ctk.CTkButton(frame, text="\u2728 Login",
                                        fg_color="#2B7A4B",
                                        hover_color="#1F5C38",
                                        height=40, corner_radius=10,
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        command=self._attempt_login)
        self.login_btn.grid(row=5, column=0, padx=20, pady=(0, 8), sticky="ew")

        self.status_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=11))
        self.status_label.grid(row=6, column=0, padx=20, pady=(4, 10))

        ctk.CTkLabel(frame, text="Contact ImranDev3 to obtain a license",
                      font=ctk.CTkFont(size=10), text_color="#555555").grid(
            row=7, column=0, pady=(0, 12))

        self._center()

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"+{(sw - w)//2}+{(sh - h)//2}")

    def _attempt_login(self):
        key = self.key_var.get().strip()
        if not key:
            self.status_label.configure(text="Please enter a license key", text_color="#FF9800")
            return

        self.login_btn.configure(state="disabled", text="\u23f3 Verifying...")
        self.status_label.configure(text="Connecting to KeyAuth...", text_color="#888888")

        def worker():
            try:
                ka = KeyAuthApp(KEYAUTH_NAME, KEYAUTH_OWNERID, KEYAUTH_SECRET, KEYAUTH_VERSION)
                init_res = ka.init()
                if not init_res.get("success"):
                    msg = init_res.get("message", "Initialization failed")
                    self.after(0, lambda: self._fail(msg))
                    return

                lic_res = ka.license(key)
                if lic_res.get("success"):
                    self.after(0, self._success)
                else:
                    msg = lic_res.get("message", "Invalid license key")
                    self.after(0, lambda: self._fail(msg))
            except Exception as e:
                self.after(0, lambda: self._fail(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _success(self):
        if self.remember_var.get():
            save_license_key(self.key_var.get().strip())
        else:
            clear_license_key()
        self._auth_result = True
        self.destroy()

    def _fail(self, msg: str):
        self.login_btn.configure(state="normal", text="\u2728 Login")
        self.status_label.configure(text=f"\u274c {msg}", text_color="#F44336")

    def run(self):
        self.mainloop()
        return self._auth_result


# ───────────────────────── TAG POPUP ───────────────────────────

class TagPopup(ctk.CTkToplevel):
    def __init__(self, parent, current_tags: list, on_done):
        super().__init__(parent)
        self.on_done = on_done
        self.title("Manage Tags")
        self.geometry("300x200")
        self.resizable(False, False)

        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text="Select or type a tag",
                      font=ctk.CTkFont(size=13)).pack(pady=(8, 8))

        self.tag_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(frame, textvariable=self.tag_var,
                                   placeholder_text="Custom tag...", corner_radius=6)
        self.entry.pack(fill="x", padx=10, pady=4)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=8)

        for tag in TAG_PRESETS:
            ctk.CTkButton(btn_frame, text=tag, corner_radius=6,
                           font=ctk.CTkFont(size=10), width=60, height=24,
                           fg_color=_tag_color(tag),
                           command=lambda t=tag: self._pick(t)).pack(
                side="left", padx=2)

        ctk.CTkButton(frame, text="Add Tag", corner_radius=8,
                       command=self._add).pack(pady=6)

    def _pick(self, tag: str):
        self.on_done(tag)
        self.destroy()

    def _add(self):
        t = self.tag_var.get().strip()
        if t:
            self.on_done(t)
        self.destroy()


# ──────────────────── PROFILE ROW ──────────────────────────────

class ProfileRow(ctk.CTkFrame):
    def __init__(self, parent, index: int, config: ProfileConfig, **kwargs):
        super().__init__(parent, corner_radius=8, **kwargs)
        self.index = index
        self.config = config
        self._advanced_shown = False
        self._advanced_frame: Optional[ctk.CTkFrame] = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(2, weight=1)

        self.check_var = ctk.BooleanVar(value=self.config.enabled)
        ctk.CTkCheckBox(self, text="", variable=self.check_var,
                         width=20, corner_radius=4).grid(
            row=0, column=0, padx=(8, 4), pady=6, sticky="w")

        ctk.CTkLabel(self, text=f"Profile {self.index}",
                      font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=1, padx=(0, 6), pady=6, sticky="w")

        self.tag_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tag_container.grid(row=0, column=2, padx=4, pady=6, sticky="w")
        self._render_tags()

        ctk.CTkButton(self, text="\u2699\ufe0f", width=30, height=24,
                       corner_radius=6, font=ctk.CTkFont(size=14),
                       command=self._toggle_advanced).grid(
            row=0, column=3, padx=(4, 8), pady=6, sticky="e")

    def _render_tags(self):
        for w in self.tag_container.winfo_children():
            w.destroy()
        for tag in self.config.tags:
            lbl = ctk.CTkLabel(self.tag_container, text=tag, corner_radius=4,
                                fg_color=_tag_color(tag),
                                text_color="white",
                                font=ctk.CTkFont(size=10),
                                padx=6, pady=1)
            lbl.pack(side="left", padx=2)

        ctk.CTkButton(self.tag_container, text="+", width=22, height=18,
                       corner_radius=4, font=ctk.CTkFont(size=12),
                       command=self._add_tag).pack(side="left", padx=2)

    def _add_tag(self):
        TagPopup(self.master.master, self.config.tags, self._tag_callback)

    def _tag_callback(self, tag: str):
        if tag and tag not in self.config.tags:
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
        self._advanced_frame.grid_columnconfigure((1, 3, 5), weight=1)

        self.proxy_var = ctk.BooleanVar(value=self.config.proxy.enabled)
        ctk.CTkCheckBox(self._advanced_frame, text="Proxy",
                         variable=self.proxy_var, corner_radius=4).grid(
            row=0, column=0, padx=(6, 4), pady=4, sticky="w")

        ctk.CTkLabel(self._advanced_frame, text="IP:Port",
                      font=ctk.CTkFont(size=11)).grid(
            row=0, column=1, padx=(0, 2), pady=4, sticky="w")
        self.proxy_ip_entry = ctk.CTkEntry(self._advanced_frame,
                                            placeholder_text="IP", width=110, corner_radius=6)
        self.proxy_ip_entry.insert(0, self.config.proxy.ip)
        self.proxy_ip_entry.grid(row=0, column=2, padx=2, pady=4, sticky="w")

        self.proxy_port_entry = ctk.CTkEntry(self._advanced_frame,
                                              placeholder_text="Port", width=55, corner_radius=6)
        self.proxy_port_entry.insert(0, self.config.proxy.port)
        self.proxy_port_entry.grid(row=0, column=3, padx=2, pady=4, sticky="w")

        ctk.CTkLabel(self._advanced_frame, text="User",
                      font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, padx=(6, 2), pady=4, sticky="w")
        self.proxy_user_entry = ctk.CTkEntry(self._advanced_frame,
                                              placeholder_text="user", width=100, corner_radius=6)
        self.proxy_user_entry.insert(0, self.config.proxy.username)
        self.proxy_user_entry.grid(row=1, column=1, padx=2, pady=4, sticky="ew")

        ctk.CTkLabel(self._advanced_frame, text="Pass",
                      font=ctk.CTkFont(size=11)).grid(
            row=1, column=2, padx=(6, 2), pady=4, sticky="w")
        self.proxy_pass_entry = ctk.CTkEntry(self._advanced_frame,
                                              placeholder_text="pass", width=100, corner_radius=6,
                                              show="*")
        self.proxy_pass_entry.insert(0, self.config.proxy.password)
        self.proxy_pass_entry.grid(row=1, column=3, padx=2, pady=4, sticky="ew")

        self.ua_var = ctk.StringVar(value=self.config.user_agent)
        ctk.CTkLabel(self._advanced_frame, text="UA",
                      font=ctk.CTkFont(size=11)).grid(
            row=2, column=0, padx=(6, 2), pady=4, sticky="w")
        ctk.CTkEntry(self._advanced_frame, textvariable=self.ua_var,
                      placeholder_text="Custom User-Agent...", corner_radius=6).grid(
            row=2, column=1, columnspan=3, padx=2, pady=4, sticky="ew")

        self.mute_var = ctk.BooleanVar(value=self.config.mute_audio)
        ctk.CTkCheckBox(self._advanced_frame, text="Mute Audio",
                         variable=self.mute_var, corner_radius=4).grid(
            row=3, column=0, padx=(6, 4), pady=4, sticky="w")

        self.ext_var = ctk.StringVar(value=self.config.extension_path)
        ctk.CTkLabel(self._advanced_frame, text="Ext Path",
                      font=ctk.CTkFont(size=11)).grid(
            row=4, column=0, padx=(6, 2), pady=4, sticky="w")
        ctk.CTkEntry(self._advanced_frame, textvariable=self.ext_var,
                      placeholder_text="C:/extensions/my-ext", corner_radius=6).grid(
            row=4, column=1, columnspan=3, padx=2, pady=4, sticky="ew")

    def save_state(self):
        self.config.enabled = self.check_var.get()
        if self._advanced_frame and self._advanced_shown:
            self.config.proxy.enabled = self.proxy_var.get()
            self.config.proxy.ip = self.proxy_ip_entry.get().strip()
            self.config.proxy.port = self.proxy_port_entry.get().strip()
            self.config.proxy.username = self.proxy_user_entry.get().strip()
            self.config.proxy.password = self.proxy_pass_entry.get().strip()
            self.config.user_agent = self.ua_var.get().strip()
            self.config.mute_audio = self.mute_var.get()
            self.config.extension_path = self.ext_var.get().strip()


# ──────────────────── LOG CONSOLE ─────────────────────────────

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


# ──────────────────── MAIN DASHBOARD ──────────────────────────

class Dashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chrome Commander Pro")
        self.geometry("860+50+50")
        self.resizable(False, False)

        self.config: AppConfig = load_config()
        self.profile_rows: list[ProfileRow] = []
        self._dynamic_count = 12
        self._before_windows = []
        self._launching = False

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._repopulate_rows()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.geometry("860x900")

        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=(14, 4), padx=20, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(title_frame, text="Chrome Commander Pro",
                      font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="w")
        ctk.CTkLabel(title_frame, text="\U0001f513 Licensed",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#2EC4B6").grid(
            row=1, column=0, sticky="w")

        # Search + Tags
        top_bar = ctk.CTkFrame(self, corner_radius=10)
        top_bar.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top_bar, text="\U0001f50d",
                      font=ctk.CTkFont(size=16)).grid(
            row=0, column=0, padx=(10, 4), pady=8, sticky="w")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_rows())
        ctk.CTkEntry(top_bar, placeholder_text="Search profiles by name or tag...",
                      textvariable=self.search_var, corner_radius=8).grid(
            row=0, column=1, padx=4, pady=8, sticky="ew")

        self._build_tag_filters(top_bar)

        # Profiles container
        profile_label_frame = ctk.CTkFrame(self, fg_color="transparent")
        profile_label_frame.grid(row=2, column=0, padx=20, pady=(0, 2), sticky="ew")
        profile_label_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(profile_label_frame, text="Profiles",
                      font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w")

        ctk.CTkButton(profile_label_frame, text="Select All", width=80, corner_radius=6,
                       command=self._select_all).pack(side="right", padx=(4, 0))
        ctk.CTkButton(profile_label_frame, text="Deselect All", width=80, corner_radius=6,
                       command=self._deselect_all).pack(side="right")

        self.profiles_container = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.profiles_container.grid(row=3, column=0, padx=20, pady=(0, 8), sticky="nsew")

        # Add profile button
        self.add_btn = ctk.CTkButton(self, text="+ Add Profile", corner_radius=8,
                                      fg_color="#3A3A5C", hover_color="#2A2A4C",
                                      font=ctk.CTkFont(size=12), height=28,
                                      command=self._add_profile)
        self.add_btn.grid(row=4, column=0, padx=20, pady=(0, 6), sticky="ew")

        # URLs
        urls_frame = ctk.CTkFrame(self, corner_radius=10)
        urls_frame.grid(row=5, column=0, padx=20, pady=(0, 6), sticky="ew")
        urls_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(urls_frame, text="Target URLs",
                      font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(6, 2), sticky="w")

        self.url_entries = []
        defaults = self.config.urls
        for i in range(5):
            ctk.CTkLabel(urls_frame, text=f"{i + 1}.", width=20, anchor="e",
                          font=ctk.CTkFont(size=12)).grid(
                row=i + 1, column=0, padx=(10, 2), pady=2, sticky="e")
            entry = ctk.CTkEntry(urls_frame, placeholder_text=f"URL {i + 1}...", corner_radius=6)
            if i < len(defaults):
                entry.insert(0, defaults[i])
            entry.grid(row=i + 1, column=1, padx=(0, 10), pady=2, sticky="ew")
            self.url_entries.append(entry)

        # Settings row
        settings_frame = ctk.CTkFrame(self, corner_radius=10)
        settings_frame.grid(row=6, column=0, padx=20, pady=(0, 6), sticky="ew")
        settings_frame.grid_columnconfigure(3, weight=1)

        self.human_var = ctk.BooleanVar(value=self.config.human_like_delay)
        ctk.CTkCheckBox(settings_frame, text="Human-Like Launch",
                         variable=self.human_var, corner_radius=4).grid(
            row=0, column=0, padx=(10, 4), pady=10, sticky="w")

        ctk.CTkLabel(settings_frame, text="Delay:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=1, padx=(4, 2), pady=10, sticky="w")

        self.delay_min_var = ctk.StringVar(value=str(self.config.delay_min))
        ctk.CTkEntry(settings_frame, textvariable=self.delay_min_var,
                      width=40, corner_radius=6).grid(
            row=0, column=2, padx=2, pady=10, sticky="w")

        ctk.CTkLabel(settings_frame, text="-", font=ctk.CTkFont(size=14)).grid(
            row=0, column=3, padx=0, pady=10, sticky="w")

        self.delay_max_var = ctk.StringVar(value=str(self.config.delay_max))
        ctk.CTkEntry(settings_frame, textvariable=self.delay_max_var,
                      width=40, corner_radius=6).grid(
            row=0, column=4, padx=2, pady=10, sticky="w")

        ctk.CTkLabel(settings_frame, text="sec", font=ctk.CTkFont(size=12)).grid(
            row=0, column=5, padx=(0, 10), pady=10, sticky="w")

        # Action buttons
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=7, column=0, padx=20, pady=(0, 4), sticky="ew")
        action_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(action_frame, text="\U0001f680 Launch Selected Profiles",
                       fg_color="#2B7A4B", hover_color="#1F5C38",
                       height=42, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._launch_profiles).grid(
            row=0, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkButton(action_frame, text="\U0001f9f0 Tile Windows",
                       fg_color="#3A3A5C", hover_color="#2A2A4C",
                       height=42, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._tile_windows).grid(
            row=0, column=1, padx=4, sticky="ew")

        ctk.CTkButton(action_frame, text="\U0001f6d1 Force Close All",
                       fg_color="#B32424", hover_color="#8A1B1B",
                       height=42, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._force_close).grid(
            row=0, column=2, padx=(4, 0), sticky="ew")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, corner_radius=6)
        self.progress_bar.grid(row=8, column=0, padx=20, pady=(4, 2), sticky="ew")
        self.progress_bar.set(0)

        # Log console
        self.log_console = LogConsole(self, height=110, corner_radius=8)
        self.log_console.grid(row=9, column=0, padx=20, pady=(2, 12), sticky="ew")

        ctk.CTkLabel(self, text="Developed by ImranDev3  |  github.com/ImranDev3",
                      font=ctk.CTkFont(size=10), text_color="#555555").grid(
            row=10, column=0, pady=(0, 6))

    def _build_tag_filters(self, parent):
        self.tag_filter_var = ctk.StringVar(value="All")

        def on_tag_change(_=None):
            self._filter_rows()

        ctk.CTkLabel(parent, text="Tags:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, padx=(8, 2), pady=8, sticky="w")

        tags = ["All"] + TAG_PRESETS
        menu = ctk.CTkOptionMenu(parent, values=tags, variable=self.tag_filter_var,
                                  width=100, corner_radius=8,
                                  command=on_tag_change)
        menu.grid(row=0, column=3, padx=(0, 8), pady=8, sticky="w")

    def _repopulate_rows(self, filter_text: str = "", filter_tag: str = ""):
        for row in self.profile_rows:
            row.destroy()
        self.profile_rows.clear()

        total = self._dynamic_count
        for i in range(total):
            idx = i + 1
            name = f"Profile {idx}"
            if filter_text and filter_text.lower() not in name.lower():
                tags_text = " ".join(self.config.profiles[i].tags).lower()
                if filter_text.lower() not in tags_text:
                    continue
            if filter_tag and filter_tag != "All":
                if filter_tag not in self.config.profiles[i].tags:
                    continue

            if i >= len(self.config.profiles):
                self.config.profiles.append(ProfileConfig())

            row = ProfileRow(self.profiles_container, idx, self.config.profiles[i])
            row.pack(fill="x", padx=4, pady=2)
            self.profile_rows.append(row)

    def _filter_rows(self):
        text = self.search_var.get().strip()
        tag = self.tag_filter_var.get()
        self._repopulate_rows(text, tag)

    def _add_profile(self):
        self._dynamic_count += 1
        idx = self._dynamic_count
        for _ in range(len(self.config.profiles), idx):
            self.config.profiles.append(ProfileConfig())
        self._repopulate_rows(self.search_var.get().strip(), self.tag_filter_var.get())

    def _select_all(self):
        for row in self.profile_rows:
            row.check_var.set(True)

    def _deselect_all(self):
        for row in self.profile_rows:
            row.check_var.set(False)

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

        def worker():
            launch_all(
                profiles=selected,
                urls=urls,
                user_data_dir=CHROME_DATA_DIR,
                human_like=human,
                delay_min=dmin,
                delay_max=dmax,
                progress_cb=lambda v: self.after(0, lambda: self.progress_bar.set(v)),
                log_cb=lambda m, l: self.after(0, lambda: self.log_console.write(m, l)),
            )
            self._launching = False

        threading.Thread(target=worker, daemon=True).start()

    def _force_close(self):
        self._save_all()
        force_close(log_cb=lambda m, l: self.after(0, lambda: self.log_console.write(m, l)))

    def _tile_windows(self):
        tile_chrome_windows(self._before_windows,
                            log_cb=lambda m, l: self.after(0, lambda: self.log_console.write(m, l)))

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
