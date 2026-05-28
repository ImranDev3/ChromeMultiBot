import subprocess
import random
import time
import math
import json
import ctypes
import ctypes.wintypes
from pathlib import Path
from typing import List, Callable

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
_REAL_USER_DATA = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"

_WEnumProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
user32 = ctypes.windll.user32


def get_chrome_user_data_dir() -> Path:
    return _REAL_USER_DATA if _REAL_USER_DATA.exists() else (Path.home() / ".chromemultibot" / "chrome_data")


def detect_profiles() -> list[dict]:
    """
    Detect existing Chrome profiles from the real User Data directory.
    Returns a list of dicts: {id, dir, name}
    The first profile (Default) is always included.
    """
    profiles = []
    ud = get_chrome_user_data_dir()

    if not ud.exists():
        return [{"id": 1, "dir": "Default", "name": "Default"}]

    try:
        local_state = ud / "Local State"
        if local_state.exists():
            data = json.loads(local_state.read_text(encoding="utf-8"))
            info = data.get("profile", {}).get("info_cache", {})
            for prof_dir, meta in info.items():
                if prof_dir == "Default":
                    profiles.append({"id": 1, "dir": "Default", "name": meta.get("name", "Default")})
                elif prof_dir.startswith("Profile "):
                    num = int(prof_dir.split()[-1]) + 1
                    profiles.append({"id": num, "dir": prof_dir, "name": meta.get("name", prof_dir)})

    except Exception:
        pass

    if not profiles:
        profiles.append({"id": 1, "dir": "Default", "name": "Default"})
        for i in range(1, 12):
            pdir = f"Profile {i}"
            if (ud / pdir).exists():
                profiles.append({"id": i + 1, "dir": pdir, "name": pdir})

    profiles.sort(key=lambda p: p["id"])
    return profiles


def launch_single(profile_dir: str, urls: List[str], user_data_dir: Path,
                  proxy: str = "", mute: bool = False) -> bool:
    if not urls:
        return False
    try:
        cmd = [CHROME_EXE]
        cmd.append(f'--user-data-dir={user_data_dir}')
        cmd.append(f'--profile-directory="{profile_dir}"')
        cmd.append("--no-first-run")
        cmd.append("--disable-search-engine-choice-screen")

        if mute:
            cmd.append("--mute-audio")

        if proxy:
            cmd.append(f'--proxy-server=http://{proxy}')

        cmd.append("--new-window")
        cmd.append(urls[0])
        for u in urls[1:]:
            cmd.append(u)

        subprocess.Popen(cmd, shell=False)
        return True
    except Exception:
        return False


def launch_all(profiles: List[tuple], urls: List[str], user_data_dir: Path,
               human_like: bool = False, delay_min: int = 2, delay_max: int = 5,
               progress_cb: Callable = None, log_cb: Callable = None) -> List[str]:
    total = len(profiles)
    launched = []
    user_data_dir.mkdir(parents=True, exist_ok=True)

    for idx, (prof_dir, proxy, mute, name) in enumerate(profiles):
        if log_cb:
            log_cb(f"Launching {name}...", "info")
        ok = launch_single(prof_dir, urls, user_data_dir, proxy, mute)
        if ok:
            launched.append(prof_dir)
            if log_cb:
                log_cb(f"{name} opened with {len(urls)} tab(s)", "success")
        else:
            if log_cb:
                log_cb(f"{name} failed to launch", "error")

        if progress_cb:
            progress_cb((idx + 1) / total)

        if human_like and idx < total - 1:
            delay = random.uniform(delay_min, delay_max)
            if log_cb:
                log_cb(f"Anti-bot delay: waiting {delay:.1f}s...", "info")
            time.sleep(delay)

    if log_cb:
        log_cb(f"Done \u2014 {len(launched)}/{total} profile(s) launched", "success")
    return launched


def force_close(log_cb: Callable = None):
    try:
        r = subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"],
                           capture_output=True, text=True, timeout=10)
        msg = r.stdout.strip() or r.stderr.strip()
        if log_cb:
            if "success" in msg.lower() or "sent" in msg.lower():
                log_cb("All Chrome processes terminated", "success")
            else:
                log_cb(msg or "No Chrome processes found", "info")
    except subprocess.TimeoutExpired:
        if log_cb:
            log_cb("Force close timed out", "error")
    except Exception as e:
        if log_cb:
            log_cb(f"Force close error: {e}", "error")


def _enum_chrome_windows() -> list:
    handles = []

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetClassNameW(hwnd, buf, 512)
            if buf.value and "Chrome_WidgetWin" in buf.value:
                handles.append(hwnd)
        return True

    user32.EnumWindows(_WEnumProc(callback), 0)
    return handles


def tile_windows(before: list, log_cb: Callable = None):
    after = _enum_chrome_windows()
    new_windows = [h for h in after if h not in before]
    if not new_windows:
        if log_cb:
            log_cb("No new Chrome windows to tile", "info")
        return

    count = len(new_windows)
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)

    for i, hwnd in enumerate(new_windows):
        col = i % cols
        row = i // cols
        user32.MoveWindow(hwnd, col * (sw // cols), row * (sh // rows),
                          sw // cols, sh // rows, True)

    if log_cb:
        log_cb(f"Tiled {count} window(s) in a {rows}x{cols} grid", "success")


def snapshot_windows() -> list:
    return _enum_chrome_windows()
