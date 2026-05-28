import subprocess
import os
import json
import random
import time
import math
import ctypes
import ctypes.wintypes
from pathlib import Path
from typing import List, Optional, Callable

from .config import ProfileConfig, CHROME_DATA_DIR, EXTENSIONS_DIR

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

_WEnumProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
user32 = ctypes.windll.user32


def _build_extension(path: str, profile_idx: int, username: str, password: str) -> Optional[Path]:
    if not username:
        return None
    ext_dir = EXTENSIONS_DIR / f"Profile_{profile_idx}"
    ext_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "name": "Proxy Auth",
        "version": "1.0",
        "manifest_version": 2,
        "permissions": ["webRequest", "webRequestBlocking", "<all_urls>"],
        "background": {"scripts": ["bg.js"], "persistent": True},
    }
    js = (
        'chrome.webRequest.onAuthRequired.addListener(\n'
        '  function(d) {\n'
        f'    return {{authCredentials: {{username: "{username}", password: "{password}"}}}};\n'
        '  },\n'
        '  {urls: ["<all_urls>"]},\n'
        '  ["blocking"]\n'
        ');\n'
    )
    (ext_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ext_dir / "bg.js").write_text(js, encoding="utf-8")
    return ext_dir


def _profile_dir_name(idx: int) -> str:
    if idx == 1:
        return "Default"
    return f"Profile {idx - 1}"


def launch_single(profile_idx: int, profile: ProfileConfig, urls: List[str],
                  user_data_dir: Path, log_cb: Callable = None) -> bool:
    if not urls:
        return False
    try:
        cmd = [CHROME_EXE]
        cmd.append(f'--user-data-dir={user_data_dir}')
        cmd.append(f'--profile-directory="{_profile_dir_name(profile_idx)}"')
        cmd.append("--no-first-run")
        cmd.append("--disable-search-engine-choice-screen")

        if profile.mute_audio:
            cmd.append("--mute-audio")

        if profile.proxy.enabled and profile.proxy.ip:
            proxy_str = f"{profile.proxy.ip}:{profile.proxy.port}"
            cmd.append(f'--proxy-server=http://{proxy_str}')
            if profile.proxy.username:
                ext = _build_extension("", profile_idx, profile.proxy.username, profile.proxy.password)
                if ext:
                    cmd.append(f'--load-extension={ext}')

        if profile.extension_path:
            p = Path(profile.extension_path)
            if p.exists():
                cmd.append(f'--load-extension={p}')

        if profile.user_agent:
            cmd.append(f'--user-agent="{profile.user_agent}"')

        cmd.append("--new-window")
        cmd.append(urls[0])
        for u in urls[1:]:
            cmd.append(u)

        subprocess.Popen(cmd, shell=False)
        if log_cb:
            log_cb(f"Profile {profile_idx} launched ({len(urls)} tabs)", "success")
        return True
    except Exception as e:
        if log_cb:
            log_cb(f"Profile {profile_idx} error: {e}", "error")
        return False


def launch_all(profiles: List[tuple], urls: List[str], user_data_dir: Path,
               human_like: bool = False, delay_min: int = 2, delay_max: int = 5,
               progress_cb: Callable = None, log_cb: Callable = None) -> List[int]:
    total = len(profiles)
    launched = []
    user_data_dir.mkdir(parents=True, exist_ok=True)

    for idx, (profile_idx, profile) in enumerate(profiles):
        if log_cb:
            log_cb(f"Launching Profile {profile_idx}...", "info")
        ok = launch_single(profile_idx, profile, urls, user_data_dir, log_cb)
        if ok:
            launched.append(profile_idx)
        if progress_cb:
            progress_cb((idx + 1) / total)
        if human_like and idx < total - 1:
            delay = random.uniform(delay_min, delay_max)
            if log_cb:
                log_cb(f"Waiting {delay:.1f}s (anti-bot delay)...", "info")
            time.sleep(delay)

    if log_cb:
        log_cb(f"Done — {len(launched)}/{total} profiles launched", "success")
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


def tile_chrome_windows(before: list, log_cb: Callable = None):
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
    cw = sw // cols
    ch = sh // rows

    for i, hwnd in enumerate(new_windows):
        col = i % cols
        row = i // cols
        user32.MoveWindow(hwnd, col * cw, row * ch, cw, ch, True)

    if log_cb:
        log_cb(f"Tiled {count} window(s) in a {rows}x{cols} grid", "success")


def get_current_chrome_windows() -> list:
    return _enum_chrome_windows()
