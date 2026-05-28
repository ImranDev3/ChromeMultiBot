import threading
import json
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from .launcher import launch_all, force_close, tile_windows, snapshot_windows, detect_profiles, get_chrome_user_data_dir

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

CONFIG_DIR = Path.home() / ".chromemultibot"
CONFIG_FILE = CONFIG_DIR / "settings.json"

TAG_PRESETS = ["Trading", "Social", "Work", "Banking", "Shopping", "Entertainment"]
TAG_COLORS = {
    "Trading": "#FF6B35", "Social": "#4361EE", "Work": "#2EC4B6",
    "Banking": "#E71D36", "Shopping": "#FF9F1C", "Entertainment": "#9D4EDD",
}


def _tag_c(tag):
    return TAG_COLORS.get(tag, "#6C757D")


def _load_settings():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_settings(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


class TagDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_tags, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Add Tag")
        self.geometry("300x190")
        self.resizable(False, False)

        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(frame, text="Choose or type a tag",
                      font=ctk.CTkFont(size=13)).pack(pady=(8, 8))

        self.tag_var = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.tag_var,
                      placeholder_text="Custom tag...", corner_radius=6).pack(fill="x", padx=8, pady=4)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=6)

        for tag in TAG_PRESETS:
            if tag not in current_tags:
                ctk.CTkButton(btn_frame, text=tag, corner_radius=6,
                               font=ctk.CTkFont(size=10), width=60, height=22,
                               fg_color=_tag_c(tag),
                               command=lambda t=tag: self._pick(t)).pack(side="left", padx=2)

        ctk.CTkButton(frame, text="Add", corner_radius=8,
                       command=self._add).pack(pady=4)

    def _pick(self, tag):
        self.callback(tag)
        self.destroy()

    def _add(self):
        t = self.tag_var.get().strip()
        if t:
            self.callback(t)
        self.destroy()


class ProfileRow(ctk.CTkFrame):
    def __init__(self, parent, profile_info: dict, data: dict = None, **kwargs):
        super().__init__(parent, corner_radius=8, **kwargs)
        self.profile = profile_info
        self._data = data or {"checked": False, "proxy": "", "tags": []}
        self._build()

    def _build(self):
        self.grid_columnconfigure(2, weight=1)

        self.check_var = ctk.BooleanVar(value=self._data.get("checked", False))
        ctk.CTkCheckBox(self, text="", variable=self.check_var,
                         width=20, corner_radius=4).grid(
            row=0, column=0, padx=(8, 4), pady=6, sticky="w")

        ctk.CTkLabel(self, text=self.profile["name"],
                      font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=1, padx=(0, 6), pady=6, sticky="w")

        self.proxy_var = ctk.StringVar(value=self._data.get("proxy", ""))
        ctk.CTkEntry(self, textvariable=self.proxy_var,
                      placeholder_text="IP:Port", width=120, corner_radius=6).grid(
            row=0, column=2, padx=4, pady=6, sticky="w")

        self.tag_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tag_container.grid(row=0, column=3, padx=4, pady=6, sticky="w")
        self._render_tags()

    def _render_tags(self):
        for w in self.tag_container.winfo_children():
            w.destroy()
        for tag in self._data.get("tags", []):
            ctk.CTkLabel(self.tag_container, text=tag, corner_radius=4,
                          fg_color=_tag_c(tag), text_color="white",
                          font=ctk.CTkFont(size=10), padx=6, pady=1).pack(side="left", padx=2)

        ctk.CTkButton(self.tag_container, text="+", width=22, height=18,
                       corner_radius=4, font=ctk.CTkFont(size=12),
                       command=self._add_tag).pack(side="left", padx=2)

    def _add_tag(self):
        TagDialog(self.master.master, self._data.get("tags", []), self._on_tag)

    def _on_tag(self, tag):
        if tag and tag not in self._data.get("tags", []):
            self._data.setdefault("tags", []).append(tag)
            self._render_tags()

    def collect(self) -> dict:
        return {
            "profile_dir": self.profile["dir"],
            "name": self.profile["name"],
            "checked": self.check_var.get(),
            "proxy": self.proxy_var.get().strip(),
            "tags": self._data.get("tags", []),
        }


class LogConsole(ctk.CTkTextbox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(state="disabled")

    def write(self, msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        emoji = {"info": "\u2139\ufe0f", "success": "\u2705",
                 "error": "\u274c", "warning": "\u26a0\ufe0f"}
        line = f"[{ts}] {emoji.get(level, '\u2139\ufe0f')} {msg}\n"
        self.configure(state="normal")
        self.insert("end", line)
        self.see("end")
        self.configure(state="disabled")


class Dashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chrome Commander Pro")
        self.resizable(False, False)

        self.rows: list[ProfileRow] = []
        self._window_snapshot = []
        self._launching = False

        self.detected_profiles = detect_profiles()
        self.user_data_dir = get_chrome_user_data_dir()
        self.settings = _load_settings()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._repopulate()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.geometry("860+60+40")

        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=(14, 4), padx=20, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(title_frame, text="Chrome Commander Pro",
                      font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_frame, text=f"\U0001f513 {len(self.detected_profiles)} profiles detected",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#2EC4B6").grid(row=1, column=0, sticky="w")

        top_bar = ctk.CTkFrame(self, corner_radius=10)
        top_bar.grid(row=1, column=0, padx=20, pady=(0, 6), sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top_bar, text="\U0001f50d", font=ctk.CTkFont(size=16)).grid(row=0, column=0, padx=(10, 4), pady=8, sticky="w")
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        ctk.CTkEntry(top_bar, textvariable=self.search_var,
                      placeholder_text="Search profiles by name or tag...",
                      corner_radius=8).grid(row=0, column=1, padx=4, pady=8, sticky="ew")

        urls_frame = ctk.CTkFrame(self, corner_radius=10)
        urls_frame.grid(row=2, column=0, padx=20, pady=(0, 4), sticky="ew")
        urls_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(urls_frame, text="Target URLs",
                      font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(6, 2), sticky="w")

        defaults = self.settings.get("urls", [
            "https://www.google.com", "https://www.facebook.com",
            "https://mail.google.com", "https://www.youtube.com",
            "https://www.github.com",
        ])
        self.url_entries = []
        for i in range(5):
            ctk.CTkLabel(urls_frame, text=f"{i + 1}.", width=20, anchor="e",
                          font=ctk.CTkFont(size=12)).grid(row=i + 1, column=0, padx=(10, 2), pady=2, sticky="e")
            e = ctk.CTkEntry(urls_frame, placeholder_text=f"URL {i + 1}...", corner_radius=6)
            if i < len(defaults):
                e.insert(0, defaults[i])
            e.grid(row=i + 1, column=1, padx=(0, 10), pady=2, sticky="ew")
            self.url_entries.append(e)

        settings = ctk.CTkFrame(self, corner_radius=10)
        settings.grid(row=3, column=0, padx=20, pady=(0, 4), sticky="ew")
        settings.grid_columnconfigure(4, weight=1)

        self.human_var = ctk.BooleanVar(value=self.settings.get("human", False))
        ctk.CTkCheckBox(settings, text="Human-Like Launch",
                         variable=self.human_var, corner_radius=4).grid(
            row=0, column=0, padx=(10, 4), pady=8, sticky="w")
        ctk.CTkLabel(settings, text="Delay:", font=ctk.CTkFont(size=12)).grid(row=0, column=1, padx=(2, 2), pady=8, sticky="w")
        self.dmin_var = ctk.StringVar(value=str(self.settings.get("dmin", 2)))
        ctk.CTkEntry(settings, textvariable=self.dmin_var, width=40, corner_radius=6).grid(row=0, column=2, padx=2, pady=8, sticky="w")
        ctk.CTkLabel(settings, text="-", font=ctk.CTkFont(size=14)).grid(row=0, column=3, padx=0, pady=8, sticky="w")
        self.dmax_var = ctk.StringVar(value=str(self.settings.get("dmax", 5)))
        ctk.CTkEntry(settings, textvariable=self.dmax_var, width=40, corner_radius=6).grid(row=0, column=4, padx=2, pady=8, sticky="w")
        ctk.CTkLabel(settings, text="sec", font=ctk.CTkFont(size=12)).grid(row=0, column=5, padx=(0, 10), pady=8, sticky="w")

        self.mute_var = ctk.BooleanVar(value=self.settings.get("mute", False))
        ctk.CTkCheckBox(settings, text="Mute Audio", variable=self.mute_var, corner_radius=4).grid(
            row=0, column=6, padx=(10, 10), pady=8, sticky="w")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=4, column=0, padx=20, pady=(0, 2), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Profiles", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w")
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")
        ctk.CTkButton(btn_frame, text="Select All", width=80, corner_radius=6,
                       command=self._select_all).pack(side="left", padx=(0, 4))
        ctk.CTkButton(btn_frame, text="Deselect All", width=80, corner_radius=6,
                       command=self._deselect_all).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll.grid(row=5, column=0, padx=20, pady=(0, 4), sticky="nsew")

        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.grid(row=6, column=0, padx=20, pady=(0, 4), sticky="ew")
        ctk.CTkButton(add_frame, text="+ Add Profile", corner_radius=8,
                       fg_color="#3A3A5C", hover_color="#2A2A4C",
                       font=ctk.CTkFont(size=12), height=28,
                       command=self._add_profile).pack(fill="x")

        action = ctk.CTkFrame(self, fg_color="transparent")
        action.grid(row=7, column=0, padx=20, pady=(0, 4), sticky="ew")
        action.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(action, text="\U0001f680 Launch Selected", fg_color="#2B7A4B",
                       hover_color="#1F5C38", height=42, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._launch).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(action, text="\U0001f9f0 Tile Windows", fg_color="#3A3A5C",
                       hover_color="#2A2A4C", height=42, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._tile).grid(row=0, column=1, padx=3, sticky="ew")
        ctk.CTkButton(action, text="\U0001f6d1 Force Close All", fg_color="#B32424",
                       hover_color="#8A1B1B", height=42, corner_radius=10,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._kill).grid(row=0, column=2, padx=(3, 0), sticky="ew")

        self.progress = ctk.CTkProgressBar(self, corner_radius=6)
        self.progress.grid(row=8, column=0, padx=20, pady=(2, 2), sticky="ew")
        self.progress.set(0)

        self.log = LogConsole(self, height=120, corner_radius=8)
        self.log.grid(row=9, column=0, padx=20, pady=(2, 10), sticky="ew")

        ctk.CTkLabel(self, text="Developed by ImranDev3  |  github.com/ImranDev3",
                      font=ctk.CTkFont(size=10), text_color="#555555").grid(row=10, column=0, pady=(0, 6))

    def _repopulate(self, search: str = ""):
        for r in self.rows:
            r.destroy()
        self.rows.clear()

        for prof in self.detected_profiles:
            pid = prof["id"]
            pname = prof["name"]
            if search and search.lower() not in str(pid) and search.lower() not in pname.lower():
                continue
            row = ProfileRow(self.scroll, prof)
            row.pack(fill="x", padx=4, pady=2)
            self.rows.append(row)

    def _filter(self):
        self._repopulate(self.search_var.get().strip())

    def _add_profile(self):
        next_id = max(p["id"] for p in self.detected_profiles) + 1
        pdir = f"Profile {next_id - 1}"
        self.detected_profiles.append({"id": next_id, "dir": pdir, "name": f"Profile {next_id}"})
        self._repopulate(self.search_var.get().strip())

    def _select_all(self):
        for r in self.rows:
            r.check_var.set(True)

    def _deselect_all(self):
        for r in self.rows:
            r.check_var.set(False)

    def _collect_urls(self):
        return [e.get().strip() for e in self.url_entries if e.get().strip()]

    def _collect_profiles(self):
        result = []
        for r in self.rows:
            d = r.collect()
            if d["checked"]:
                result.append((d["profile_dir"], d["proxy"], self.mute_var.get(), d["name"]))
        return result

    def _launch(self):
        if self._launching:
            return
        self._save()
        selected = self._collect_profiles()
        if not selected:
            self.log.write("No profiles selected", "warning")
            return
        urls = self._collect_urls()
        if not urls:
            self.log.write("No URLs entered", "warning")
            return

        self._window_snapshot = snapshot_windows()
        human = self.human_var.get()
        dmin = int(self.dmin_var.get() or 2)
        dmax = int(self.dmax_var.get() or 5)
        self._launching = True
        self.log.write(f"Launching {len(selected)} profile(s)...", "info")

        def worker():
            launch_all(selected, urls, self.user_data_dir, human, dmin, dmax,
                       lambda v: self.after(0, lambda: self.progress.set(v)),
                       lambda m, l: self.after(0, lambda: self.log.write(m, l)))
            self._launching = False

        threading.Thread(target=worker, daemon=True).start()

    def _kill(self):
        self._save()
        force_close(lambda m, l: self.after(0, lambda: self.log.write(m, l)))

    def _tile(self):
        tile_windows(self._window_snapshot,
                     lambda m, l: self.after(0, lambda: self.log.write(m, l)))

    def _save(self):
        _save_settings({
            "urls": self._collect_urls(),
            "human": self.human_var.get(),
            "mute": self.mute_var.get(),
            "dmin": int(self.dmin_var.get() or 2),
            "dmax": int(self.dmax_var.get() or 5),
        })

    def _on_close(self):
        self._save()
        self.destroy()
