from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError

import pytest

import dbackup_mcp.api as api_module
from dbackup_mcp.api import DBackupClient, DBackupError, MAX_JSON_RESPONSE_BYTES
from dbackup_mcp.config import Settings


def client(tmp_path: Path) -> DBackupClient:
    key = tmp_path / "api-key"
    key.write_text("test-token", encoding="utf-8")
    key.chmod(0o600)
    return DBackupClient(Settings("https://backup.example.com", key))


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int = -1) -> bytes:
        return self.payload if size < 0 else self.payload[:size]


def test_successful_malformed_json_returns_bounded_generic_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_module, "urlopen", lambda *args, **kwargs: FakeResponse(b"not-json-secret-body"))
    with pytest.raises(DBackupError, match="invalid JSON") as exc:
        client(tmp_path).request("GET", "/health")
    assert "secret-body" not in str(exc.value)


def test_successful_oversized_json_is_rejected_before_parsing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b'"' + (b"x" * MAX_JSON_RESPONSE_BYTES) + b'"'
    monkeypatch.setattr(api_module, "urlopen", lambda *args, **kwargs: FakeResponse(payload))
    with pytest.raises(DBackupError, match="too large"):
        client(tmp_path).request("GET", "/storage/id/files")


def test_http_error_does_not_return_secret_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise HTTPError(
            "https://backup.example.com/api/jobs",
            400,
            "Bad Request",
            hdrs=None,
            fp=BytesIO(b'{"message":"invalid configuration","password":"do-not-leak"}'),
        )

    monkeypatch.setattr(api_module, "urlopen", fail)
    with pytest.raises(DBackupError) as exc:
        client(tmp_path).request("POST", "/jobs", body={})
    text = str(exc.value)
    assert "invalid configuration" in text
    assert "do-not-leak" not in text


def test_client_validates_settings_before_accepting_base_url(tmp_path: Path) -> None:
    key = tmp_path / "api-key"
    key.write_text("test-token", encoding="utf-8")
    key.chmod(0o600)
    with pytest.raises(ValueError, match=r"HTTP\(S\) origin"):
        DBackupClient(Settings("file:///tmp/dbackup", key))
