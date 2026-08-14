from __future__ import annotations

from typing import Any

from .api import DBackupClient
from .models import (
    AdapterCreateInput,
    AdapterTestInput,
    AdapterUpdateInput,
    ArchiveBrowseInput,
    BackupVerifyInput,
    CredentialGeneratedSshInput,
    CredentialSecretFileInput,
    CredentialSecretFileUpdateInput,
    JobSpec,
    JobUpdateInput,
    NotificationLogsInput,
    RestoreFilesInput,
    RestorePlanInput,
    RestoreStartInput,
)


class DBackupService:
    def __init__(self, client: DBackupClient):
        self.client = client

    def status(self) -> Any:
        return self.client.request("GET", "/health")

    def capabilities(self) -> dict[str, Any]:
        return {
            "dbackupContract": "3.2.0",
            "transport": "stdio",
            "apiBoundary": "DBackup public REST API plus source-verified DBackup 3.2.0 routes used for directory and granular-restore workflows",
            "apiKeyPermissionsForFullSurface": [
                "jobs:read", "jobs:write", "jobs:execute", "history:read",
                "sources:view", "sources:write", "destinations:read", "destinations:write",
                "notifications:read", "notifications:write", "storage:read", "storage:restore",
                "credentials:read", "credentials:write", "credentials:delete",
            ],
            "unsupportedRestDiscovery": [
                "encryption profiles",
                "retention policies",
                "naming templates",
                "notification templates",
                "schedule presets",
                "exclude-pattern presets",
            ],
            "excludedTools": [
                "raw_http",
                "api_key_admin",
                "credential_reveal",
                "recovery_kit_download",
                "database_table_rows",
                "backup_download",
                "backup_delete",
                "system_tasks",
                "user_rbac_sso_admin",
            ],
        }

    def jobs_list(self) -> Any:
        return self.client.request("GET", "/jobs")

    def job_get(self, job_id: str) -> Any:
        jobs = self.jobs_list()
        for job in jobs if isinstance(jobs, list) else []:
            if job.get("id") == job_id:
                return job
        raise ValueError(f"Job not found: {job_id}")

    def job_plan(self, spec: JobSpec) -> dict[str, Any]:
        warnings: list[str] = []
        checks: dict[str, Any] = {
            "databaseSource": None,
            "directorySources": [],
            "destinations": [],
        }

        database_adapters = {item.get("id"): item for item in self.adapters_list("database", None) or []}
        source_adapters = {item.get("id"): item for item in self.adapters_list("storage", "SOURCE") or []}
        destination_adapters = {item.get("id"): item for item in self.adapters_list("storage", "DESTINATION") or []}

        if spec.source_id:
            if spec.source_id not in database_adapters:
                raise ValueError(f"Database source adapter not found: {spec.source_id}")
            checks["databaseSource"] = spec.source_id
            if spec.databases:
                discovered = self.adapter_databases(spec.source_id)
                available = set(discovered.get("databases", [])) if isinstance(discovered, dict) else set()
                missing = sorted(set(spec.databases) - available)
                if missing:
                    raise ValueError(f"Requested database not available on source {spec.source_id}: {', '.join(missing)}")

        destination_ids = {destination.config_id for destination in spec.destinations}
        for destination_id in sorted(destination_ids):
            if destination_id not in destination_adapters:
                raise ValueError(f"Storage destination adapter not found: {destination_id}")
        checks["destinations"] = sorted(destination_ids)

        for source in spec.sources:
            if source.config_id not in source_adapters:
                raise ValueError(f"Directory SOURCE adapter not found: {source.config_id}")
            if source.config_id in destination_ids:
                raise ValueError(f"A storage adapter cannot be both source and destination in one job: {source.config_id}")
            self.adapter_browse(source.config_id, source.path)
            checks["directorySources"].append(source.config_id)
            if source.stop_containers:
                warnings.append(f"Directory source {source.path} may stop containers during backup")

        checks["directorySources"].sort()
        if spec.backup_mode == "INCREMENTAL" and not spec.sources:
            warnings.append("Incremental mode only benefits directory sources; database dumps remain full")
        return {"valid": True, "payload": spec.to_api_payload(), "checks": checks, "warnings": warnings}

    def job_create(self, spec: JobSpec) -> Any:
        return self.client.request("POST", "/jobs", body=spec.to_api_payload())

    def job_update(self, spec: JobUpdateInput) -> Any:
        return self.client.request("PUT", f"/jobs/{spec.id}", body=spec.to_api_payload())

    def job_clone(self, job_id: str) -> Any:
        return self.client.request("POST", f"/jobs/{job_id}/clone")

    def job_set_enabled(self, job_id: str, enabled: bool) -> Any:
        return self.client.request("PUT", f"/jobs/{job_id}", body={"enabled": enabled})

    def job_delete(self, job_id: str, confirm: bool) -> Any:
        if not confirm:
            raise ValueError("confirm=true is required")
        return self.client.request("DELETE", f"/jobs/{job_id}")

    def job_run(self, job_id: str) -> Any:
        return self.client.request("POST", f"/jobs/{job_id}/run")

    def history_list(self, limit: int) -> Any:
        result = self.client.request("GET", "/history")
        if isinstance(result, dict) and isinstance(result.get("executions"), list):
            result = {**result, "executions": result["executions"][:limit]}
        return result

    def execution_get(self, execution_id: str, log_limit: int = 100) -> Any:
        result = self.client.request(
            "GET",
            f"/executions/{execution_id}",
            query={"includeLogs": "true" if log_limit > 0 else "false"},
        )
        if isinstance(result, dict) and isinstance(result.get("data"), dict):
            data = dict(result["data"])
            logs = data.get("logs")
            if log_limit <= 0:
                data.pop("logs", None)
            elif isinstance(logs, list):
                data["logs"] = logs[-log_limit:]
            result = {**result, "data": data}
        return result

    def execution_cancel(self, execution_id: str, confirm: bool) -> Any:
        if not confirm:
            raise ValueError("confirm=true is required")
        return self.client.request("POST", f"/executions/{execution_id}/cancel")

    def adapters_list(self, type_: str, role: str | None) -> Any:
        return self.client.request("GET", "/adapters", query={"type": type_, "role": role})

    def adapter_get(self, adapter_id: str) -> Any:
        for type_ in ("database", "storage", "notification"):
            for item in self.adapters_list(type_, None) or []:
                if item.get("id") == adapter_id:
                    return item
        raise ValueError(f"Adapter not found: {adapter_id}")

    def adapter_create(self, spec: AdapterCreateInput) -> Any:
        body: dict[str, Any] = {"name": spec.name, "type": spec.type, "adapterId": spec.adapter_id, "config": spec.config}
        if spec.primary_credential_id is not None: body["primaryCredentialId"] = spec.primary_credential_id
        if spec.ssh_credential_id is not None: body["sshCredentialId"] = spec.ssh_credential_id
        if spec.storage_role is not None: body["storageRole"] = spec.storage_role
        return self.client.request("POST", "/adapters", body=body)

    def adapter_update(self, spec: AdapterUpdateInput) -> Any:
        body = {
            "name": spec.name,
            "config": spec.config,
            "primaryCredentialId": spec.primary_credential_id,
            "sshCredentialId": spec.ssh_credential_id,
            "storageRole": spec.storage_role,
        }
        return self.client.request("PUT", f"/adapters/{spec.id}", body={k: v for k, v in body.items() if v is not None})

    def adapter_clone(self, adapter_id: str) -> Any:
        return self.client.request("POST", f"/adapters/{adapter_id}/clone")

    def adapter_delete(self, adapter_id: str, confirm: bool) -> Any:
        if not confirm:
            raise ValueError("confirm=true is required")
        return self.client.request("DELETE", f"/adapters/{adapter_id}")

    def adapter_test(self, spec: AdapterTestInput) -> Any:
        body: dict[str, Any] = {"adapterId": spec.adapter_id, "config": spec.config}
        if spec.config_id: body["configId"] = spec.config_id
        if spec.primary_credential_id: body["primaryCredentialId"] = spec.primary_credential_id
        if spec.ssh_credential_id: body["sshCredentialId"] = spec.ssh_credential_id
        return self.client.request("POST", "/adapters/test-connection", body=body)

    def adapter_browse(self, adapter_id: str, path: str) -> Any:
        return self.client.request("GET", f"/adapters/{adapter_id}/browse", query={"path": path})

    def adapter_databases(self, adapter_id: str) -> Any:
        return self.client.request("GET", f"/adapters/{adapter_id}/databases")

    def adapter_database_stats(self, source_id: str) -> Any:
        return self.client.request("POST", "/adapters/database-stats", body={"sourceId": source_id})

    def adapter_health(self, adapter_id: str) -> Any:
        return self.client.request("GET", f"/adapters/{adapter_id}/health-history", query={"limit": 50})

    def adapter_version_history(self, adapter_id: str, limit: int) -> Any:
        return self.client.request("GET", f"/adapters/{adapter_id}/version-history", query={"limit": limit})

    def notification_logs(self, spec: NotificationLogsInput) -> Any:
        return self.client.request(
            "GET",
            "/notification-logs",
            query={
                "page": spec.page,
                "pageSize": spec.page_size,
                "adapterId": spec.adapter_id,
                "eventType": spec.event_type,
                "status": spec.status,
                "executionId": spec.execution_id,
            },
        )

    def notification_log_get(self, log_id: str) -> Any:
        return self.client.request("GET", f"/notification-logs/{log_id}")

    def credentials_list(self) -> Any:
        return self.client.request("GET", "/credentials")

    def credential_get(self, credential_id: str) -> Any:
        return self.client.request("GET", f"/credentials/{credential_id}")

    def credential_usage(self, credential_id: str) -> Any:
        return self.client.request("GET", f"/credentials/{credential_id}/usage")

    def credential_create_from_secret_file(self, spec: CredentialSecretFileInput) -> Any:
        payload = self.client.settings.read_credential_payload(spec.secret_file)
        return self.client.request("POST", "/credentials", body={"name": spec.name, "type": spec.type, "description": spec.description, "data": payload})

    def credential_update_from_secret_file(self, spec: CredentialSecretFileUpdateInput) -> Any:
        payload = self.client.settings.read_credential_payload(spec.secret_file)
        body: dict[str, Any] = {"data": payload}
        if spec.name is not None: body["name"] = spec.name
        if spec.description is not None: body["description"] = spec.description
        return self.client.request("PUT", f"/credentials/{spec.id}", body=body)

    def credential_create_generated_ssh(self, spec: CredentialGeneratedSshInput) -> Any:
        data: dict[str, Any] = {"username": spec.username, "authType": "privateKey", "generate": {"keyType": spec.key_type}}
        if spec.comment: data["generate"]["comment"] = spec.comment
        body = {"name": spec.name, "type": "SSH_KEY", "description": spec.description, "data": data}
        return self.client.request("POST", "/credentials", body=body)

    def credential_delete(self, credential_id: str, confirm: bool) -> Any:
        if not confirm:
            raise ValueError("confirm=true is required")
        return self.client.request("DELETE", f"/credentials/{credential_id}")

    def storage_history(self, destination_id: str, days: int) -> Any:
        return self.client.request("GET", f"/storage/{destination_id}/history", query={"days": days})

    def storage_check_path(self, destination_id: str, path: str) -> Any:
        return self.client.request("POST", f"/storage/{destination_id}/check-path", body={"path": path})

    def backups_list(self, destination_id: str, limit: int = 200, type_filter: str | None = None) -> Any:
        result = self.client.request(
            "GET",
            f"/storage/{destination_id}/files",
            query={"typeFilter": type_filter},
        )
        return result[:limit] if isinstance(result, list) else result

    def backup_verify(self, spec: BackupVerifyInput) -> Any:
        path = "verify-async" if spec.async_mode else "verify"
        return self.client.request("POST", f"/storage/{spec.id}/{path}", body={"file": spec.file})

    def archive_browse(self, spec: ArchiveBrowseInput) -> Any:
        body: dict[str, Any] = {"file": spec.file}
        if spec.job_source_id: body["jobSourceId"] = spec.job_source_id
        if spec.prefix is not None: body["prefix"] = spec.prefix
        if spec.profile_id_override: body["profileIdOverride"] = spec.profile_id_override
        return self.client.request("POST", f"/storage/{spec.id}/browse-archive", body=body)

    def restore_plan(self, spec: RestorePlanInput) -> Any:
        analysis = self.client.request("POST", f"/storage/{spec.id}/analyze", body={"file": spec.file})
        return {"analysis": analysis, "request": self._restore_payload(spec), "requiresConfirmation": True}

    @staticmethod
    def _restore_payload(spec: RestorePlanInput) -> dict[str, Any]:
        body: dict[str, Any] = {"file": spec.file, "scope": spec.scope}
        if spec.target_source_id: body["targetSourceId"] = spec.target_source_id
        if spec.target_database_name: body["targetDatabaseName"] = spec.target_database_name
        if spec.database_mapping: body["databaseMapping"] = spec.database_mapping
        return body

    def restore_start(self, spec: RestoreStartInput) -> Any:
        if not spec.confirm:
            raise ValueError("confirm=true is required")
        return self.client.request("POST", f"/storage/{spec.id}/restore", body=self._restore_payload(spec))

    def restore_files(self, spec: RestoreFilesInput) -> Any:
        if not spec.dry_run and not spec.confirm:
            raise ValueError("confirm=true is required unless dry_run=true")
        body: dict[str, Any] = {
            "file": spec.file,
            "selections": [selection.model_dump(exclude_none=True) for selection in spec.selections],
            "target": {"kind": "storage", "configId": spec.target_config_id, "basePath": spec.target_base_path},
        }
        if spec.exclude_patterns: body["excludePatterns"] = spec.exclude_patterns
        if spec.profile_id_override: body["profileIdOverride"] = spec.profile_id_override
        if spec.dry_run: body["dryRun"] = True
        return self.client.request("POST", f"/storage/{spec.id}/restore-files", body=body)
