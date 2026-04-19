from __future__ import annotations

import json
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_DIR = Path.home() / ".logshield"
CONFIG_FILE = CONFIG_DIR / "config.json"
RAPIDAPI_URL = "https://logshield.p.rapidapi.com"
RAPIDAPI_HOST = "logshield.p.rapidapi.com"
LOCAL_URL = "http://localhost:8000"
LOCAL_PROXY_SECRET = "dev-secret-change-in-prod"


@dataclass
class Credentials:
    rapidapi_key: str
    api_url: str = RAPIDAPI_URL
    api_host: str = RAPIDAPI_HOST
    local: bool = False


def local_credentials() -> "Credentials":
    return Credentials(
        rapidapi_key=LOCAL_PROXY_SECRET,
        api_url=LOCAL_URL,
        api_host="localhost",
        local=True,
    )


def save(creds: Credentials) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(creds), indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def load() -> Credentials | None:
    if not CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return Credentials(**data)
    except (json.JSONDecodeError, TypeError):
        return None


def clear() -> bool:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        return True
    return False
