from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

_SAFE_FILE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key_file: Path
    request_timeout_seconds: float = 15.0
    credential_secret_dir: Path | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        raw_secret_dir = os.environ.get("DBACKUP_CREDENTIAL_SECRET_DIR", "").strip()
        settings = cls(
            os.environ.get("DBACKUP_BASE_URL", "").rstrip("/"),
            Path(os.environ.get("DBACKUP_API_KEY_FILE", "")),
            float(os.environ.get("DBACKUP_REQUEST_TIMEOUT_SECONDS", "15")),
            Path(raw_secret_dir) if raw_secret_dir else None,
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        parsed = urlsplit(self.base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("DBACKUP_BASE_URL must be an HTTP(S) origin without credentials, path, query, or fragment")
        if not 0 < self.request_timeout_seconds <= 120:
            raise ValueError("DBACKUP_REQUEST_TIMEOUT_SECONDS must be greater than 0 and at most 120")
        self._validate_private_file(self.api_key_file)
        self.read_api_key()
        if self.credential_secret_dir is not None:
            self._validate_private_directory(self.credential_secret_dir)

    @staticmethod
    def _validate_private_file(path: Path, label: str = "DBackup API-key file") -> None:
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise ValueError(f"{label} does not exist: {path}") from exc
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"{label} must be a regular file")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError(f"{label} must not have group or other permissions")
        if not 1 <= info.st_size <= 4096:
            raise ValueError(f"{label} has an invalid size")

    @staticmethod
    def _validate_private_directory(path: Path) -> None:
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise ValueError(f"DBackup credential secret directory does not exist: {path}") from exc
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError("DBackup credential secret directory must be a directory")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError("DBackup credential secret directory must not have group or other permissions")

    def read_api_key(self) -> str:
        self._validate_private_file(self.api_key_file)
        value = self.api_key_file.read_text(encoding="utf-8").strip()
        if not value or any(char.isspace() for char in value):
            raise ValueError("DBackup API-key file must contain one non-empty token")
        return value

    def read_credential_payload(self, file_name: str) -> dict[str, Any]:
        if self.credential_secret_dir is None:
            raise ValueError("DBACKUP_CREDENTIAL_SECRET_DIR is not configured")
        if not _SAFE_FILE_NAME.fullmatch(file_name):
            raise ValueError("Credential secret file name must be a safe basename")
        self._validate_private_directory(self.credential_secret_dir)
        path = self.credential_secret_dir / file_name
        self._validate_private_file(path, "DBackup credential secret file")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Credential secret file must contain one JSON object") from exc
        if not isinstance(payload, dict) or not payload:
            raise ValueError("Credential secret file must contain one non-empty JSON object")
        return payload
