import hashlib
import hmac
import json
from pathlib import Path

from .config import CONFIG_DIR

LICENSE_FILE = CONFIG_DIR / "license.json"
TRIAL_MAX_PROFILES = 3

# Must match keygen.py
_SEED = b"CMB@2024#Secure!Key$For%License^Generation&Only*Developer"


def _derive_secret() -> bytes:
    return hashlib.sha256(_SEED).digest()


def _generate_expected_key(owner: str) -> str:
    secret = _derive_secret()
    data = owner.strip().lower().encode("utf-8")
    raw = hmac.new(secret, data, hashlib.sha256).hexdigest().upper()
    groups = [raw[i:i+8] for i in range(0, 24, 8)]
    return f"CHMB-{groups[0]}-{groups[1]}-{groups[2]}"


class LicenseManager:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if LICENSE_FILE.exists():
            try:
                return json.loads(LICENSE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"activated": False, "owner": "", "key": ""}

    def _save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        LICENSE_FILE.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    @property
    def is_activated(self) -> bool:
        return self._data.get("activated", False)

    @property
    def max_profiles(self) -> int:
        return 12 if self.is_activated else TRIAL_MAX_PROFILES

    @property
    def owner(self) -> str:
        return self._data.get("owner", "")

    def activate(self, key: str, owner: str) -> bool:
        expected = _generate_expected_key(owner)
        if key.strip().upper() == expected:
            self._data["activated"] = True
            self._data["owner"] = owner.strip()
            self._data["key"] = key.strip()
            self._save()
            return True
        return False

    def deactivate(self):
        self._data = {"activated": False, "owner": "", "key": ""}
        self._save()
