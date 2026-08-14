from __future__ import annotations

import json
from pathlib import Path

import pytest

from dbackup_mcp.config import Settings
from dbackup_mcp.models import AdapterCreateInput


def test_adapter_config_rejects_secret_bearing_keys() -> None:
    with pytest.raises(ValueError, match="secret-bearing"):
        AdapterCreateInput(name="Postgres", type="database", adapter_id="postgres", config={"host": "db", "password": "nope"})


def test_adapter_config_accepts_credential_profile_references() -> None:
    adapter = AdapterCreateInput(
        name="Postgres",
        type="database",
        adapter_id="postgres",
        config={"host": "db", "port": 5432},
        primary_credential_id="cred1",
        ssh_credential_id="ssh1",
    )
    assert adapter.primary_credential_id == "cred1"


def test_credential_secret_file_is_bounded_private_json(tmp_path: Path) -> None:
    key = tmp_path / "api-key"
    key.write_text("api-token", encoding="utf-8")
    key.chmod(0o600)
    secrets = tmp_path / "credential-inputs"
    secrets.mkdir(mode=0o700)
    item = secrets / "db-password.json"
    item.write_text(json.dumps({"username": "backup", "password": "secret"}), encoding="utf-8")
    item.chmod(0o600)
    settings = Settings("http://dbackup:3000", key, credential_secret_dir=secrets)
    settings.validate()
    assert settings.read_credential_payload("db-password.json")["username"] == "backup"
    with pytest.raises(ValueError, match="safe basename"):
        settings.read_credential_payload("../escape")


def test_credential_secret_file_permission_error_names_credential_file(tmp_path: Path) -> None:
    key = tmp_path / "api-key"
    key.write_text("api-token", encoding="utf-8")
    key.chmod(0o600)
    secrets = tmp_path / "credential-inputs"
    secrets.mkdir(mode=0o700)
    item = secrets / "credential.json"
    item.write_text(json.dumps({"username": "backup", "password": "secret"}), encoding="utf-8")
    item.chmod(0o644)
    settings = Settings("http://dbackup:3000", key, credential_secret_dir=secrets)
    settings.validate()
    with pytest.raises(ValueError, match="credential secret file.*group or other permissions"):
        settings.read_credential_payload("credential.json")
