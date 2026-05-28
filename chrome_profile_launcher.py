import subprocess
import sys

try:
    import customtkinter as ctk
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

class ChromeProfileLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chrome Profile Launcher")
        self.geometry("680x720")
        self.resizable(False, False)

        self.profile_vars = [ctk.BooleanVar(value=False) for _ in range(12)]

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Chrome Profile Launcher", font=ctk.CTkFont(size=22, weight="bold"))
        title.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="n")

        profiles_frame = ctk.CTkFrame(self, corner_radius=12)
        profiles_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        profiles_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(profiles_frame, text="Chrome Profiles", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, pady=(12, 6), padx=10, sticky="w"
        )

        btn_frame = ctk.CTkFrame(profiles_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=(0, 8), padx=10, sticky="w")
        ctk.CTkButton(btn_frame, text="Select All", width=100, command=self._select_all).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="Deselect All", width=100, command=self._deselect_all).pack(side="left")

        cb_frame = ctk.CTkFrame(profiles_frame, fg_color="transparent")
        cb_frame.grid(row=2, column=0, padx=10, pady=(0, 12), sticky="ew")
        cb_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for i, var in enumerate(self.profile_vars):
            row = i // 4
            col = i % 4
            cb = ctk.CTkCheckBox(cb_frame, text=f"Profile {i + 1}", variable=var, corner_radius=6)
            cb.grid(row=row, column=col, padx=6, pady=4, sticky="w")

        urls_frame = ctk.CTkFrame(self, corner_radius=12)
        urls_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        urls_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(urls_frame, text="Website URLs", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, columnspan=2, pady=(12, 6), padx=10, sticky="w"
        )

        self.url_entries = []
        default_urls = ["https://www.google.com", "https://www.facebook.com", "https://mail.google.com",
                        "https://www.youtube.com", "https://www.github.com"]
        for i in range(5):
            label = ctk.CTkLabel(urls_frame, text=f"URL {i + 1}:", width=60, anchor="e")
            label.grid(row=i + 1, column=0, padx=(10, 4), pady=4, sticky="e")
            entry = ctk.CTkEntry(urls_frame, placeholder_text=f"Enter URL {i + 1}...", corner_radius=8)
            entry.insert(0, default_urls[i])
            entry.grid(row=i + 1, column=1, padx=(0, 10), pady=4, sticky="ew")
            self.url_entries.append(entry)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=3, column=0, pady=(8, 20), padx=20, sticky="ew")
        action_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(action_frame, text="\U0001f680 Launch Selected Profiles", fg_color="#2b7a4b",
                       hover_color="#1f5c38", height=42, corner_radius=10,
                       command=self._launch_profiles).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(action_frame, text="\U0001f6d1 Force Close All", fg_color="#b32424",
                       hover_color="#8a1b1b", height=42, corner_radius=10,
                       command=self._force_close).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _get_urls(self):
        return [e.get().strip() for e in self.url_entries if e.get().strip()]

    def _select_all(self):
        for var in self.profile_vars:
            var.set(True)

    def _deselect_all(self):
        for var in self.profile_vars:
            var.set(False)

    def _launch_profiles(self):
        urls = self._get_urls()
        if not urls:
            return

        for i, var in enumerate(self.profile_vars):
            if var.get():
                profile_dir = f"Profile {i + 1}"
                cmd = [CHROME_PATH, f"--profile-directory={profile_dir}", "--new-window", urls[0]]
                for url in urls[1:]:
                    cmd.append(url)
                try:
                    subprocess.Popen(cmd)
                except Exception as e:
                    print(f"Failed to launch Profile {i + 1}: {e}")

    def _force_close(self):
        try:
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True, text=True)
        except Exception as e:
            print(f"Failed to close Chrome: {e}")


if __name__ == "__main__":
    app = ChromeProfileLauncher()
    app.mainloop()
