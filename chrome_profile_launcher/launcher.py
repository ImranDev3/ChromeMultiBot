import subprocess
import random
import time
import math
import ctypes
import ctypes.wintypes
from pathlib import Path
from typing import List, Callable, Optional

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

_WEnumProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
user32 = ctypes.windll.user32


def _profile_dir(idx: int) -> str:
    return "Default" if idx == 1 else f"Profile {idx - 1}"


def launch_single(profile_idx: int, urls: List[str], user_data_dir: Path,
                  proxy: str = "", mute: bool = False) -> bool:
    if not urls:
        return False
    try:
        cmd = [CHROME_EXE]
        cmd.append(f'--user-data-dir={user_data_dir}')
        cmd.append(f'--profile-directory="{_profile_dir(profile_idx)}"')
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
               progress_cb: Callable = None, log_cb: Callable = None) -> List[int]:
    total = len(profiles)
    launched = []
    user_data_dir.mkdir(parents=True, exist_ok=True)

    for idx, (profile_idx, proxy, mute) in enumerate(profiles):
        if log_cb:
            log_cb(f"Launching Profile {profile_idx}...", "info")
        ok = launch_single(profile_idx, urls, user_data_dir, proxy, mute)
        if ok:
            launched.append(profile_idx)
            if log_cb:
                log_cb(f"Profile {profile_idx} opened with {len(urls)} tab(s)", "success")
        else:
            if log_cb:
                log_cb(f"Profile {profile_idx} failed to launch", "error")

        if progress_cb:
            progress_cb((idx + 1) / total)

        if human_like and idx < total - 1:
            delay = random.uniform(delay_min, delay_max)
            if log_cb:
                log_cb(f"Anti-bot delay: waiting {delay:.1f}s...", "info")
            time.sleep(delay)

    if log_cb:
        log_cb(f"Done — {len(launched)}/{total} profile(s) launched", "success")
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
