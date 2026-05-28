import json
import time
import hashlib
import secrets
import requests
from urllib.parse import urlencode

API_URL = "https://keyauth.win/api/1.2/"


def _session_id() -> str:
    return secrets.token_hex(10)


def _enctype(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


class KeyAuthApp:
    def __init__(self, name: str, ownerid: str, secret: str, version: str):
        self.name = name
        self.ownerid = ownerid
        self.secret = secret
        self.version = version
        self.sessionid = _session_id()
        self.initialized = False

    def _req(self, payload: dict) -> dict:
        payload["name"] = self.name
        payload["ownerid"] = self.ownerid
        payload["ver"] = self.version
        try:
            r = requests.post(API_URL, data=payload, timeout=15)
            return r.json()
        except Exception as e:
            return {"success": False, "message": str(e)}

    def init(self) -> dict:
        data = {
            "type": "init",
            "sessionid": self.sessionid,
            "init": _enctype(self.sessionid + self.secret),
        }
        r = self._req(data)
        if r.get("success"):
            self.initialized = True
        return r

    def license(self, key: str) -> dict:
        if not self.initialized:
            self.init()
        data = {
            "type": "license",
            "key": key,
            "sessionid": self.sessionid,
            "init": _enctype(self.sessionid + self.secret),
        }
        return self._req(data)
