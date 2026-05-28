import hashlib
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".chromemultibot"
LICENSE_FILE = CONFIG_DIR / "license_config.json"

_VALID_KEYS = [
    "CHROME-PRO-ALPHA",
    "CHROME-PRO-BETA",
    "CHROME-PRO-GAMMA",
]

_VALID_HASHES = [hashlib.md5(k.encode()).hexdigest() for k in _VALID_KEYS]


def _hash_key(key: str) -> str:
    return hashlib.md5(key.strip().encode()).hexdigest()


def verify_key(key: str) -> bool:
    return _hash_key(key) in _VALID_HASHES


def save_license(key: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LICENSE_FILE.write_text(json.dumps({"key": key, "hash": _hash_key(key)}), encoding="utf-8")


def load_license() -> dict:
    if LICENSE_FILE.exists():
        try:
            data = json.loads(LICENSE_FILE.read_text(encoding="utf-8"))
            if verify_key(data.get("key", "")):
                return data
        except Exception:
            pass
    return {}


def clear_license():
    if LICENSE_FILE.exists():
        LICENSE_FILE.unlink()
