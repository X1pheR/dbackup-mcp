from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, TypeVar

import mcp.types as types
from mcp.server import Server
from pydantic import BaseModel, ValidationError

from .api import DBackupClient, DBackupError
from .config import Settings
from .models import (
    AdapterBrowseInput,
    AdapterCreateInput,
    AdapterListInput,
    AdapterTestInput,
    AdapterUpdateInput,
    ArchiveBrowseInput,
    BackupsListInput,
    BackupVerifyInput,
    ConfirmedIdInput,
    CredentialGeneratedSshInput,
    CredentialSecretFileInput,
    CredentialSecretFileUpdateInput,
    DatabaseStatsInput,
    EmptyInput,
    ExecutionGetInput,
    IdInput,
    JobEnabledInput,
    JobSpec,
    JobUpdateInput,
    NotificationLogsInput,
    RestoreFilesInput,
    RestorePlanInput,
    RestoreStartInput,
    SearchInput,
    StorageCheckPathInput,
    StorageHistoryInput,
    VersionHistoryInput,
)
from .service import DBackupService

app = Server("dbackup")
_service: DBackupService
ModelT = TypeVar("ModelT", bound=BaseModel)


def _annotations(*, read_only: bool, destructive: bool = False, idempotent: bool | None = None) -> types.ToolAnnotations:
    return types.ToolAnnotations(
        readOnlyHint=read_only,
        destructiveHint=destructive,
        idempotentHint=read_only if idempotent is None else idempotent,
        openWorldHint=False,
    )


def _tool(name: str, description: str, model: type[BaseModel], *, read_only: bool, destructive: bool = False, idempotent: bool | None = None) -> types.Tool:
    return types.Tool(name=name, description=description, inputSchema=model.model_json_schema(), annotations=_annotations(read_only=read_only, destructive=destructive, idempotent=idempotent))


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        _tool("dbackup_status", "Check DBackup health and authenticated API availability.", EmptyInput, read_only=True),
        _tool("dbackup_capabilities", "Describe the supported DBackup contract, API boundary, and deliberate exclusions.", EmptyInput, read_only=True),
        _tool("jobs_list", "List configured backup jobs with secret-bearing fields removed.", EmptyInput, read_only=True),
        _tool("job_get", "Get one backup job by ID.", IdInput, read_only=True),
        _tool("job_plan", "Validate and preview a complete database/directory backup job without changing DBackup.", JobSpec, read_only=True),
        _tool("job_create", "Create a complete database and/or directory backup job.", JobSpec, read_only=False),
        _tool("job_update", "Replace the managed configuration of an existing backup job.", JobUpdateInput, read_only=False, destructive=True),
        _tool("job_clone", "Clone an existing backup job.", IdInput, read_only=False),
        _tool("job_set_enabled", "Enable or disable an existing backup job.", JobEnabledInput, read_only=False, idempotent=True),
        _tool("job_delete", "Delete one backup job. Requires confirm=true.", ConfirmedIdInput, read_only=False, destructive=True),
        _tool("job_run", "Start one backup job manually.", IdInput, read_only=False),
        _tool("history_list", "List recent backup and restore execution history.", SearchInput, read_only=True),
        _tool("execution_get", "Get one execution with model-visible logs bounded to the requested tail length.", ExecutionGetInput, read_only=True),
        _tool("execution_cancel", "Cancel one running execution. Requires confirm=true.", ConfirmedIdInput, read_only=False, destructive=True),
        _tool("adapters_list", "List database, storage, or notification adapters with secrets removed.", AdapterListInput, read_only=True),
        _tool("adapter_get", "Get one adapter with secrets removed.", IdInput, read_only=True),
        _tool("adapter_create", "Create a database source, directory source, storage destination, or notification adapter.", AdapterCreateInput, read_only=False),
        _tool("adapter_update", "Update one adapter configuration. Secret fields are never returned.", AdapterUpdateInput, read_only=False, destructive=True),
        _tool("adapter_clone", "Clone an adapter configuration.", IdInput, read_only=False),
        _tool("adapter_delete", "Delete an unused adapter. Requires confirm=true.", ConfirmedIdInput, read_only=False, destructive=True),
        _tool("adapter_test", "Test an adapter connection without persisting a new adapter.", AdapterTestInput, read_only=True),
        _tool("adapter_browse", "Browse a storage SOURCE adapter path.", AdapterBrowseInput, read_only=True),
        _tool("adapter_databases", "List databases available through a saved database source.", IdInput, read_only=True),
        _tool("adapter_database_stats", "Return database sizes and table counts for a saved source.", DatabaseStatsInput, read_only=True),
        _tool("adapter_health", "Return recent health checks for one adapter.", IdInput, read_only=True),
        _tool("adapter_version_history", "Return bounded detected database-version history for one adapter.", VersionHistoryInput, read_only=True),
        _tool("notification_logs", "List bounded DBackup notification-delivery logs with optional filters.", NotificationLogsInput, read_only=True),
        _tool("notification_log_get", "Get one DBackup notification-delivery log entry.", IdInput, read_only=True),
        _tool("credentials_list", "List credential profile metadata without secret payloads.", EmptyInput, read_only=True),
        _tool("credential_get", "Get credential metadata, public key, and fingerprint without secret payloads.", IdInput, read_only=True),
        _tool("credential_usage", "Show where a credential profile is referenced.", IdInput, read_only=True),
        _tool("credential_create_from_secret_file", "Create a credential profile from one private JSON file inside the configured secret-input directory. Secret data is never accepted as tool input or returned.", CredentialSecretFileInput, read_only=False),
        _tool("credential_update_from_secret_file", "Update a credential profile from one private JSON file inside the configured secret-input directory. Secret data is never accepted as tool input or returned.", CredentialSecretFileUpdateInput, read_only=False, destructive=True),
        _tool("credential_create_generated_ssh", "Create an SSH credential whose private key is generated and retained by DBackup; only public metadata is returned.", CredentialGeneratedSshInput, read_only=False),
        _tool("credential_delete", "Delete an unused credential profile. Requires confirm=true.", ConfirmedIdInput, read_only=False, destructive=True),
        _tool("storage_history", "Return bounded storage-usage history for one destination.", StorageHistoryInput, read_only=True),
        _tool("storage_check_path", "Check whether a restore target path is empty, occupied, or unverified without changing it.", StorageCheckPathInput, read_only=True),
        _tool("backups_list", "List a bounded number of backup files for one storage destination.", BackupsListInput, read_only=True),
        _tool("backup_verify", "Verify one backup file; asynchronous verification is the default.", BackupVerifyInput, read_only=False, idempotent=True),
        _tool("archive_browse", "Inspect one directory level inside a backup archive without restoring it.", ArchiveBrowseInput, read_only=True),
        _tool("restore_plan", "Analyze a backup and preview a restore request without changing data.", RestorePlanInput, read_only=True),
        _tool("restore_start", "Start a database/directory restore. Requires confirm=true.", RestoreStartInput, read_only=False, destructive=True),
        _tool("restore_files", "Restore selected files from an archive. Requires confirm=true.", RestoreFilesInput, read_only=False, destructive=True),
    ]


def _validate(model: type[ModelT], arguments: Any) -> ModelT:
    return model.model_validate(arguments or {})


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    try:
        if name == "dbackup_status": result = _service.status()
        elif name == "dbackup_capabilities": result = _service.capabilities()
        elif name == "jobs_list": result = _service.jobs_list()
        elif name == "job_get": result = _service.job_get(_validate(IdInput, arguments).id)
        elif name == "job_plan": result = _service.job_plan(_validate(JobSpec, arguments))
        elif name == "job_create": result = _service.job_create(_validate(JobSpec, arguments))
        elif name == "job_update": result = _service.job_update(_validate(JobUpdateInput, arguments))
        elif name == "job_clone": result = _service.job_clone(_validate(IdInput, arguments).id)
        elif name == "job_set_enabled":
            a = _validate(JobEnabledInput, arguments); result = _service.job_set_enabled(a.id, a.enabled)
        elif name == "job_delete":
            a = _validate(ConfirmedIdInput, arguments); result = _service.job_delete(a.id, a.confirm)
        elif name == "job_run": result = _service.job_run(_validate(IdInput, arguments).id)
        elif name == "history_list": result = _service.history_list(_validate(SearchInput, arguments).limit)
        elif name == "execution_get":
            a = _validate(ExecutionGetInput, arguments); result = _service.execution_get(a.id, a.log_limit)
        elif name == "execution_cancel":
            a = _validate(ConfirmedIdInput, arguments); result = _service.execution_cancel(a.id, a.confirm)
        elif name == "adapters_list":
            a = _validate(AdapterListInput, arguments); result = _service.adapters_list(a.type, a.role)
        elif name == "adapter_get": result = _service.adapter_get(_validate(IdInput, arguments).id)
        elif name == "adapter_create": result = _service.adapter_create(_validate(AdapterCreateInput, arguments))
        elif name == "adapter_update": result = _service.adapter_update(_validate(AdapterUpdateInput, arguments))
        elif name == "adapter_clone": result = _service.adapter_clone(_validate(IdInput, arguments).id)
        elif name == "adapter_delete":
            a = _validate(ConfirmedIdInput, arguments); result = _service.adapter_delete(a.id, a.confirm)
        elif name == "adapter_test": result = _service.adapter_test(_validate(AdapterTestInput, arguments))
        elif name == "adapter_browse":
            a = _validate(AdapterBrowseInput, arguments); result = _service.adapter_browse(a.id, a.path)
        elif name == "adapter_databases": result = _service.adapter_databases(_validate(IdInput, arguments).id)
        elif name == "adapter_database_stats": result = _service.adapter_database_stats(_validate(DatabaseStatsInput, arguments).source_id)
        elif name == "adapter_health": result = _service.adapter_health(_validate(IdInput, arguments).id)
        elif name == "adapter_version_history":
            a = _validate(VersionHistoryInput, arguments); result = _service.adapter_version_history(a.id, a.limit)
        elif name == "notification_logs": result = _service.notification_logs(_validate(NotificationLogsInput, arguments))
        elif name == "notification_log_get": result = _service.notification_log_get(_validate(IdInput, arguments).id)
        elif name == "credentials_list": result = _service.credentials_list()
        elif name == "credential_get": result = _service.credential_get(_validate(IdInput, arguments).id)
        elif name == "credential_usage": result = _service.credential_usage(_validate(IdInput, arguments).id)
        elif name == "credential_create_from_secret_file": result = _service.credential_create_from_secret_file(_validate(CredentialSecretFileInput, arguments))
        elif name == "credential_update_from_secret_file": result = _service.credential_update_from_secret_file(_validate(CredentialSecretFileUpdateInput, arguments))
        elif name == "credential_create_generated_ssh": result = _service.credential_create_generated_ssh(_validate(CredentialGeneratedSshInput, arguments))
        elif name == "credential_delete":
            a = _validate(ConfirmedIdInput, arguments); result = _service.credential_delete(a.id, a.confirm)
        elif name == "storage_history":
            a = _validate(StorageHistoryInput, arguments); result = _service.storage_history(a.id, a.days)
        elif name == "storage_check_path":
            a = _validate(StorageCheckPathInput, arguments); result = _service.storage_check_path(a.id, a.path)
        elif name == "backups_list":
            a = _validate(BackupsListInput, arguments); result = _service.backups_list(a.id, a.limit, a.type_filter)
        elif name == "backup_verify": result = _service.backup_verify(_validate(BackupVerifyInput, arguments))
        elif name == "archive_browse": result = _service.archive_browse(_validate(ArchiveBrowseInput, arguments))
        elif name == "restore_plan": result = _service.restore_plan(_validate(RestorePlanInput, arguments))
        elif name == "restore_start": result = _service.restore_start(_validate(RestoreStartInput, arguments))
        elif name == "restore_files": result = _service.restore_files(_validate(RestoreFilesInput, arguments))
        else: raise ValueError(f"Unknown tool: {name}")
    except ValidationError as error:
        raise ValueError(f"Invalid tool input: {error}") from None
    except (DBackupError, ValueError) as error:
        raise RuntimeError(str(error)) from None
    return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))]


async def run_stdio(settings: Settings, service: DBackupService) -> None:
    from mcp.server.stdio import stdio_server
    global _service
    _service = service
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
