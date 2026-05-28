import subprocess
import os
import json
import random
import time
import math
import ctypes
import ctypes.wintypes
from pathlib import Path
from typing import List, Optional
from .config import ProfileConfig, CHROME_PATH, EXTENSIONS_DIR

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def _build_extension(profile_idx: int, ip: str, port: str, username: str, password: str) -> Optional[Path]:
    if not username:
        return None
    ext_dir = EXTENSIONS_DIR / f"Profile_{profile_idx}"
    ext_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "name": "Proxy Auth",
        "version": "1.0",
        "manifest_version": 2,
        "permissions": ["webRequest", "webRequestBlocking", "<all_urls>"],
        "background": {"scripts": ["bg.js"], "persistent": True}
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


def launch_single(profile_idx: int, profile: ProfileConfig, urls: List[str],
                  user_data_dir: Path, log_callback=None) -> bool:
    if not urls:
        return False

    try:
        cmd = [CHROME_EXE]

        cmd.append(f'--user-data-dir={user_data_dir}')
        cmd.append(f'--profile-directory="Profile {profile_idx}"')

        cmd.append("--no-first-run")
        cmd.append("--disable-search-engine-choice-screen")

        if profile.proxy.enabled and profile.proxy.ip:
            proxy_str = f"{profile.proxy.ip}:{profile.proxy.port}"
            cmd.append(f'--proxy-server=http://{proxy_str}')

            if profile.proxy.username:
                ext = _build_extension(profile_idx, profile.proxy.ip, profile.proxy.port,
                                        profile.proxy.username, profile.proxy.password)
                if ext:
                    cmd.append(f'--load-extension={ext}')

        cmd.append("--new-window")
        cmd.append(urls[0])
        for u in urls[1:]:
            cmd.append(u)

        subprocess.Popen(cmd, shell=False)
        if log_callback:
            log_callback(f"Profile {profile_idx} launched ({len(urls)} tabs)", "success")
        return True

    except Exception as e:
        if log_callback:
            log_callback(f"Profile {profile_idx} error: {e}", "error")
        return False


def launch_all(profiles: List[tuple], urls: List[str], user_data_dir: Path,
               human_like: bool = False, delay_min: int = 2, delay_max: int = 5,
               progress_callback=None, log_callback=None) -> List[int]:
    total = len(profiles)
    launched = []

    user_data_dir.mkdir(parents=True, exist_ok=True)

    for idx, (profile_idx, profile) in enumerate(profiles):
        if log_callback:
            log_callback(f"Launching Profile {profile_idx}...", "info")

        ok = launch_single(profile_idx, profile, urls, user_data_dir, log_callback)
        if ok:
            launched.append(profile_idx)

        if progress_callback:
            progress_callback((idx + 1) / total)

        if human_like and idx < total - 1:
            delay = random.uniform(delay_min, delay_max)
            if log_callback:
                log_callback(f"Waiting {delay:.1f}s (human-like delay)...", "info")
            time.sleep(delay)

    if log_callback:
        log_callback(f"Done — {len(launched)}/{total} profiles launched", "success")
    return launched


def force_close(log_callback=None):
    try:
        r = subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"],
                           capture_output=True, text=True, timeout=10)
        msg = r.stdout.strip() or r.stderr.strip()
        if log_callback:
            if "success" in msg.lower() or "sent" in msg.lower():
                log_callback("All Chrome processes terminated", "success")
            else:
                log_callback(msg or "No Chrome processes found", "info")
    except subprocess.TimeoutExpired:
        if log_callback:
            log_callback("Force close timed out", "error")
    except Exception as e:
        if log_callback:
            log_callback(f"Force close error: {e}", "error")


user32 = ctypes.windll.user32
_WEnumProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL,
                                 ctypes.wintypes.HWND,
                                 ctypes.wintypes.LPARAM)


def _enum_chrome_windows():
    handles = []

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetClassNameW(hwnd, buf, 512)
            cls = buf.value
            if cls and "Chrome_WidgetWin" in cls:
                handles.append(hwnd)
        return True

    user32.EnumWindows(_WEnumProc(callback), 0)
    return handles


def tile_chrome_windows(before: list, log_callback=None):
    after = _enum_chrome_windows()
    new_windows = [h for h in after if h not in before]

    if not new_windows:
        if log_callback:
            log_callback("No new Chrome windows to tile", "info")
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

    if log_callback:
        log_callback(f"Tiled {count} window(s) in a {rows}×{cols} grid", "success")


def get_current_chrome_windows():
    return _enum_chrome_windows()
