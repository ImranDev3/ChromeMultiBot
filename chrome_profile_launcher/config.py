import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List

CONFIG_DIR = Path.home() / ".chromemultibot"
CONFIG_FILE = CONFIG_DIR / "config.json"
CHROME_DATA_DIR = CONFIG_DIR / "chrome_data"
EXTENSIONS_DIR = CONFIG_DIR / "extensions"


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
    tags_pool: List[str] = field(default_factory=lambda: ["Trading", "Social", "Work", "Banking", "Shopping", "Entertainment"])


def _convert(obj):
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert(v) for v in obj]
    elif obj == "true" or obj == "false":
        return obj
    return obj


def _from_dict(data: dict, cls):
    if cls == AppConfig:
        profiles_data = data.get("profiles", [])
        profiles = []
        for pd in profiles_data:
            proxy_data = pd.get("proxy", {})
            proxy = ProxyConfig(**proxy_data)
            profiles.append(ProfileConfig(
                enabled=pd.get("enabled", False),
                tags=pd.get("tags", []),
                proxy=proxy
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
            tags_pool=data.get("tags_pool", ["Trading", "Social", "Work", "Banking", "Shopping", "Entertainment"])
        )
    return cls(**data)


def load_config() -> AppConfig:
    if CONFIG_FILE.exists():
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return _from_dict(raw, AppConfig)
        except Exception:
            pass
    return AppConfig()


def save_config(config: AppConfig):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _deep(obj):
        if isinstance(obj, (AppConfig, ProfileConfig, ProxyConfig)):
            return {k: _deep(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [_deep(v) for v in obj]
        return obj

    CONFIG_FILE.write_text(json.dumps(_deep(config), indent=2, default=str), encoding="utf-8")
