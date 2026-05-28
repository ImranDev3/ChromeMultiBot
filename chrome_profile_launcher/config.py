import json
import base64
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List

CONFIG_DIR = Path.home() / ".chromemultibot"
CONFIG_FILE = CONFIG_DIR / "config.json"
LICENSE_FILE = CONFIG_DIR / "license.dat"
LICENSE_META = CONFIG_DIR / "license_meta.json"
CHROME_DATA_DIR = CONFIG_DIR / "chrome_data"
EXTENSIONS_DIR = CONFIG_DIR / "extensions"

TRIAL_MAX_PROFILES = 3


def _obfuscate(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _deobfuscate(data: str) -> str:
    try:
        return base64.b64decode(data.encode()).decode()
    except Exception:
        return ""


def save_license_key(key: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LICENSE_FILE.write_text(_obfuscate(key), encoding="utf-8")


def load_license_key() -> str:
    if LICENSE_FILE.exists():
        return _deobfuscate(LICENSE_FILE.read_text(encoding="utf-8").strip())
    return ""


def clear_license_key():
    if LICENSE_FILE.exists():
        LICENSE_FILE.unlink()


def save_license_meta(activated: bool, owner: str = ""):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LICENSE_META.write_text(json.dumps({"activated": activated, "owner": owner}), encoding="utf-8")


def load_license_meta() -> dict:
    if LICENSE_META.exists():
        try:
            return json.loads(LICENSE_META.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"activated": False, "owner": ""}


def clear_license_meta():
    if LICENSE_META.exists():
        LICENSE_META.unlink()


@dataclass
class ProxyConfig:
    enabled: bool = False
    ip: str = ""
    port: str = ""
    username: str = ""
    password: str = ""


@dataclass
class ProfileConfig:
    enabled: bool = False
    tags: List[str] = field(default_factory=list)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    user_agent: str = ""
    mute_audio: bool = False
    extension_path: str = ""


@dataclass
class AppConfig:
    profiles: List[ProfileConfig] = field(default_factory=lambda: [ProfileConfig() for _ in range(12)])
    urls: List[str] = field(default_factory=lambda: [
        "https://www.google.com",
        "https://www.facebook.com",
        "https://mail.google.com",
        "https://www.youtube.com",
        "https://www.github.com",
    ])
    human_like_delay: bool = False
    delay_min: int = 2
    delay_max: int = 5
    tags_pool: List[str] = field(default_factory=lambda: ["Trading", "Social", "Work"])


def _from_dict(data: dict) -> AppConfig:
    profiles = []
    for pd in data.get("profiles", []):
        proxy_data = pd.get("proxy", {})
        proxy = ProxyConfig(**proxy_data)
        profiles.append(ProfileConfig(
            enabled=pd.get("enabled", False),
            tags=pd.get("tags", []),
            proxy=proxy,
            user_agent=pd.get("user_agent", ""),
            mute_audio=pd.get("mute_audio", False),
            extension_path=pd.get("extension_path", ""),
        ))
    while len(profiles) < 12:
        profiles.append(ProfileConfig())
    return AppConfig(
        profiles=profiles[:12],
        urls=data.get("urls", [
            "https://www.google.com",
            "https://www.facebook.com",
            "https://mail.google.com",
            "https://www.youtube.com",
            "https://www.github.com",
        ]),
        human_like_delay=data.get("human_like_delay", False),
        delay_min=data.get("delay_min", 2),
        delay_max=data.get("delay_max", 5),
        tags_pool=data.get("tags_pool", ["Trading", "Social", "Work"]),
    )


def load_config() -> AppConfig:
    if CONFIG_FILE.exists():
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return _from_dict(raw)
        except Exception:
            pass
    return AppConfig()


def save_config(config: AppConfig):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _deep(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: _deep(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [_deep(v) for v in obj]
        return obj

    CONFIG_FILE.write_text(json.dumps(_deep(config), indent=2, default=str), encoding="utf-8")
