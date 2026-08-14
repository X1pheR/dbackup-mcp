from __future__ import annotations

import asyncio
import os
import stat
from pathlib import Path

import pytest

from dbackup_mcp.config import Settings
from dbackup_mcp.models import JobSpec, JobSourceSpec
from dbackup_mcp.sanitize import sanitize
from dbackup_mcp.server import list_tools


DBACKUP_V32_SENSITIVE_KEYS = {
    "password", "token", "secret", "secretKey", "secretAccessKey", "accessKey",
    "accessKeyId", "apiKey", "webhookUrl", "uri", "passphrase", "privateKey",
    "sshPassword", "sshPrivateKey", "sshPassphrase", "clientSecret", "refreshToken",
    "authHeader", "accountSid", "authToken", "appToken", "botToken", "accessToken",
}


def test_sanitize_covers_dbackup_v32_sensitive_key_contract() -> None:
    payload = {key: f"value-{key}" for key in DBACKUP_V32_SENSITIVE_KEYS}
    payload["safeField"] = "safe"
    result = sanitize(payload)
    assert result == {"safeField": "safe"}


def test_sanitize_removes_secret_fields_recursively() -> None:
    payload = {
        "id": "adapter-1",
        "config": {
            "host": "db.internal",
            "username": "backup",
            "password": "secret",
            "privateKey": "pem",
            "nested": {"token": "abc", "path": "/data"},
        },
        "refreshToken": "refresh",
    }
    result = sanitize(payload)
    text = repr(result)
    assert "secret" not in text
    assert "pem" not in text
    assert "abc" not in text
    assert "refresh" not in text
    assert result["config"]["host"] == "db.internal"
    assert result["config"]["username"] == "backup"
    assert result["config"]["nested"]["path"] == "/data"


def test_settings_requires_private_api_key_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key = tmp_path / "api-key"
    key.write_text("token-value\n", encoding="utf-8")
    key.chmod(0o644)
    monkeypatch.setenv("DBACKUP_BASE_URL", "http://dbackup:3000")
    monkeypatch.setenv("DBACKUP_API_KEY_FILE", str(key))
    with pytest.raises(ValueError, match="group or other permissions"):
        Settings.from_env()

    key.chmod(0o600)
    settings = Settings.from_env()
    assert settings.read_api_key() == "token-value"
    assert stat.S_IMODE(os.stat(key).st_mode) == 0o600


def test_job_spec_supports_database_and_directory_sources() -> None:
    job = JobSpec(
        name="Example application",
        schedule="0 3 * * *",
        source_id="postgres-source",
        databases=["application"],
        sources=[
            JobSourceSpec(
                config_id="docker-files",
                path="/data/application",
                exclude_patterns=["**/cache/**"],
                stop_containers=False,
            )
        ],
        destinations=[{"config_id": "remote-sftp", "retention": {"keepDaily": 7}}],
        backup_mode="INCREMENTAL",
        full_every_days=7,
        verify_by_hash=True,
    )
    payload = job.to_api_payload()
    assert payload["sourceId"] == "postgres-source"
    assert payload["databases"] == ["application"]
    assert payload["sources"][0]["configId"] == "docker-files"
    assert payload["sources"][0]["stopContainers"] is False
    assert payload["backupMode"] == "INCREMENTAL"
    assert payload["fullEveryDays"] == 7
    assert payload["verifyByHash"] is True


def test_job_source_defaults_do_not_silently_stop_containers() -> None:
    source = JobSourceSpec(config_id="source", path="/data")
    assert source.stop_containers is False
    assert source.to_api_payload()["stopContainers"] is False


def test_tool_catalog_is_curated_and_fully_annotated() -> None:
    tools = {tool.name: tool for tool in asyncio.run(list_tools())}
    required = {
        "dbackup_status",
        "jobs_list", "job_get", "job_plan", "job_create", "job_update", "job_clone", "job_set_enabled", "job_delete", "job_run",
        "history_list", "execution_get", "execution_cancel",
        "adapters_list", "adapter_get", "adapter_create", "adapter_update", "adapter_clone", "adapter_delete", "adapter_test", "adapter_browse", "adapter_databases", "adapter_database_stats", "adapter_health",
        "credentials_list", "credential_get", "credential_usage", "credential_create_from_secret_file", "credential_update_from_secret_file", "credential_create_generated_ssh", "credential_delete",
        "backups_list", "backup_verify", "archive_browse", "restore_plan", "restore_start", "restore_files",
    }
    assert required <= set(tools)
    assert "credential_reveal" not in tools
    assert "raw_request" not in tools
    for tool in tools.values():
        annotations = tool.annotations
        assert annotations is not None
        assert annotations.readOnlyHint is not None
        assert annotations.destructiveHint is not None
        assert annotations.idempotentHint is not None
        assert annotations.openWorldHint is False


def test_destructive_tools_are_marked_destructive() -> None:
    tools = {tool.name: tool for tool in asyncio.run(list_tools())}
    for name in {"job_delete", "adapter_delete", "credential_delete", "execution_cancel", "restore_start", "restore_files"}:
        assert tools[name].annotations.destructiveHint is True


def test_public_read_tool_surface_includes_diagnostics_and_capabilities() -> None:
    tools = {tool.name: tool for tool in asyncio.run(list_tools())}
    for name in {
        "dbackup_capabilities",
        "adapter_version_history",
        "notification_logs",
        "notification_log_get",
        "storage_history",
        "storage_check_path",
    }:
        assert name in tools
        assert tools[name].annotations is not None
        assert tools[name].annotations.readOnlyHint is True


@pytest.mark.parametrize(
    "base_url",
    [
        "https://user:password@backup.example.com",
        "https://backup.example.com?token=secret",
        "https://backup.example.com#fragment",
    ],
)
def test_settings_rejects_base_url_secret_or_non_origin_components(tmp_path: Path, base_url: str) -> None:
    key = tmp_path / "api-key"
    key.write_text("token-value", encoding="utf-8")
    key.chmod(0o600)
    settings = Settings(base_url, key)
    with pytest.raises(ValueError, match=r"HTTP\(S\) origin"):
        settings.validate()
