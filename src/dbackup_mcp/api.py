from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import Settings
from .sanitize import sanitize

MAX_JSON_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_ERROR_RESPONSE_BYTES = 64 * 1024


class DBackupError(RuntimeError):
    pass


class DBackupClient:
    def __init__(self, settings: Settings):
        settings.validate()
        self.settings = settings

    def request(self, method: str, path: str, *, query: dict[str, Any] | None = None, body: Any | None = None) -> Any:
        url = f"{self.settings.base_url}/api{path}"
        if query:
            cleaned = {k: v for k, v in query.items() if v is not None}
            if cleaned:
                url = f"{url}?{urlencode(cleaned, doseq=True)}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.settings.read_api_key()}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            # Settings.validate() restricts request origins to HTTP(S).
            with urlopen(req, timeout=self.settings.request_timeout_seconds) as response:  # nosec B310
                raw = response.read(MAX_JSON_RESPONSE_BYTES + 1)
                if len(raw) > MAX_JSON_RESPONSE_BYTES:
                    raise DBackupError("DBackup API response is too large")
                if not raw:
                    return None
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise DBackupError("DBackup API returned invalid JSON") from None
                return sanitize(payload)
        except HTTPError as exc:
            message = f"DBackup API returned HTTP {exc.code}"
            try:
                raw = exc.read(MAX_ERROR_RESPONSE_BYTES + 1)
                if len(raw) <= MAX_ERROR_RESPONSE_BYTES:
                    payload = json.loads(raw.decode("utf-8"))
                    safe = sanitize(payload)
                    detail = (safe.get("error") or safe.get("message")) if isinstance(safe, dict) else None
                    if isinstance(detail, (str, int, float, bool)) and detail:
                        message += f": {detail}"
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                message = f"DBackup API returned HTTP {exc.code}"
            raise DBackupError(message) from None
        except URLError as exc:
            raise DBackupError(f"DBackup API unavailable: {exc.reason}") from None
