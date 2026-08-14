from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .sanitize import contains_secret_key


class EmptyInput(BaseModel):
    pass


class IdInput(BaseModel):
    id: str = Field(min_length=1, max_length=128)


class SearchInput(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)


class ExecutionGetInput(IdInput):
    log_limit: int = Field(default=100, ge=0, le=500)


class JobDestinationSpec(BaseModel):
    config_id: str = Field(min_length=1)
    priority: int = 0
    retention: dict[str, Any] | None = None
    retention_policy_id: str | None = None

    def to_api_payload(self) -> dict[str, Any]:
        data: dict[str, Any] = {"configId": self.config_id, "priority": self.priority}
        if self.retention is not None:
            data["retention"] = self.retention
        if self.retention_policy_id is not None:
            data["retentionPolicyId"] = self.retention_policy_id
        return data


class JobSourceSpec(BaseModel):
    config_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    priority: int = 0
    exclude_patterns: list[str] = Field(default_factory=list)
    exclude_pattern_preset_ids: list[str] = Field(default_factory=list)
    stop_containers: bool = False

    def to_api_payload(self) -> dict[str, Any]:
        return {
            "configId": self.config_id,
            "priority": self.priority,
            "path": self.path,
            "excludePatterns": self.exclude_patterns,
            "excludePatternPresetIds": self.exclude_pattern_preset_ids,
            "stopContainers": self.stop_containers,
        }


class JobSpec(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    schedule: str = Field(min_length=1, max_length=100)
    source_id: str | None = None
    databases: list[str] = Field(default_factory=list)
    destinations: list[JobDestinationSpec] = Field(min_length=1)
    sources: list[JobSourceSpec] = Field(default_factory=list)
    enabled: bool = True
    compression: Literal["NONE", "GZIP", "BROTLI"] = "GZIP"
    pg_compression: str | None = None
    encryption_profile_id: str | None = None
    notification_ids: list[str] = Field(default_factory=list)
    notification_template_ids: list[str] = Field(default_factory=list)
    notification_events: Any | None = None
    naming_template_id: str | None = None
    schedule_preset_id: str | None = None
    skip_verification: bool = False
    backup_mode: Literal["FULL", "INCREMENTAL"] = "FULL"
    full_every_days: int = Field(default=7, ge=1, le=365)
    verify_by_hash: bool = False

    @model_validator(mode="after")
    def has_source(self) -> "JobSpec":
        if not self.source_id and not self.sources:
            raise ValueError("A job needs a database source_id, one or more directory sources, or both")
        return self

    def to_api_payload(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "schedule": self.schedule,
            "databases": self.databases,
            "destinations": [d.to_api_payload() for d in self.destinations],
            "sources": [s.to_api_payload() for s in self.sources],
            "enabled": self.enabled,
            "compression": self.compression,
            "skipVerification": self.skip_verification,
            "backupMode": self.backup_mode,
            "fullEveryDays": self.full_every_days,
            "verifyByHash": self.verify_by_hash,
        }
        mapping = {
            "sourceId": self.source_id,
            "pgCompression": self.pg_compression,
            "encryptionProfileId": self.encryption_profile_id,
            "notificationEvents": self.notification_events,
            "namingTemplateId": self.naming_template_id,
            "schedulePresetId": self.schedule_preset_id,
        }
        data.update({k: v for k, v in mapping.items() if v is not None})
        if self.notification_ids:
            data["notificationIds"] = self.notification_ids
        if self.notification_template_ids:
            data["notificationTemplateIds"] = self.notification_template_ids
        return data


class JobUpdateInput(JobSpec):
    id: str = Field(min_length=1, max_length=128)


class JobEnabledInput(IdInput):
    enabled: bool


class ConfirmedIdInput(IdInput):
    confirm: bool = False


class AdapterListInput(BaseModel):
    type: Literal["database", "storage", "notification"]
    role: Literal["DESTINATION", "SOURCE"] | None = None


class AdapterCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: Literal["database", "storage", "notification"]
    adapter_id: str = Field(min_length=1, max_length=100)
    config: dict[str, Any] = Field(default_factory=dict)
    primary_credential_id: str | None = None
    ssh_credential_id: str | None = None
    storage_role: Literal["DESTINATION", "SOURCE"] | None = None

    @model_validator(mode="after")
    def no_inline_secrets(self) -> "AdapterCreateInput":
        if contains_secret_key(self.config):
            raise ValueError("Adapter config contains secret-bearing fields; use credential profile references")
        return self


class AdapterUpdateInput(IdInput):
    name: str | None = None
    config: dict[str, Any] | None = None
    primary_credential_id: str | None = None
    ssh_credential_id: str | None = None
    storage_role: Literal["DESTINATION", "SOURCE"] | None = None

    @model_validator(mode="after")
    def no_inline_secrets(self) -> "AdapterUpdateInput":
        if self.config is not None and contains_secret_key(self.config):
            raise ValueError("Adapter config contains secret-bearing fields; use credential profile references")
        return self


class AdapterTestInput(BaseModel):
    adapter_id: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    config_id: str | None = None
    primary_credential_id: str | None = None
    ssh_credential_id: str | None = None

    @model_validator(mode="after")
    def no_inline_secrets(self) -> "AdapterTestInput":
        if contains_secret_key(self.config):
            raise ValueError("Adapter config contains secret-bearing fields; use credential profile references")
        return self


class AdapterBrowseInput(IdInput):
    path: str = "/"


class DatabaseStatsInput(BaseModel):
    source_id: str = Field(min_length=1)


class VersionHistoryInput(IdInput):
    limit: int = Field(default=100, ge=1, le=200)


class NotificationLogsInput(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    adapter_id: str | None = None
    event_type: str | None = None
    status: str | None = None
    execution_id: str | None = None


class StorageHistoryInput(IdInput):
    days: int = Field(default=30, ge=1, le=365)


class StorageCheckPathInput(IdInput):
    path: str = Field(min_length=1, max_length=4096)


class CredentialSecretFileInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: Literal["USERNAME_PASSWORD", "SSH_KEY", "ACCESS_KEY", "TOKEN", "SMTP"]
    secret_file: str = Field(min_length=1, max_length=128)
    description: str | None = None


class CredentialSecretFileUpdateInput(IdInput):
    secret_file: str = Field(min_length=1, max_length=128)
    name: str | None = Field(default=None, max_length=200)
    description: str | None = None


class CredentialGeneratedSshInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    username: str = Field(min_length=1, max_length=200)
    key_type: Literal["ed25519", "rsa-4096", "ecdsa-p256", "ecdsa-p384"] = "ed25519"
    comment: str | None = Field(default=None, max_length=120)
    description: str | None = None


class ArchiveBrowseInput(IdInput):
    file: str = Field(min_length=1)
    job_source_id: str | None = None
    prefix: str | None = None
    profile_id_override: str | None = None


class BackupsListInput(IdInput):
    limit: int = Field(default=200, ge=1, le=1000)
    type_filter: str | None = Field(default=None, max_length=100)


class BackupVerifyInput(IdInput):
    file: str = Field(min_length=1)
    async_mode: bool = True


class RestorePlanInput(IdInput):
    file: str = Field(min_length=1)
    scope: Literal["all", "databases", "files"] = "all"
    target_source_id: str | None = None
    target_database_name: str | None = None
    database_mapping: dict[str, str] = Field(default_factory=dict)


class RestoreStartInput(RestorePlanInput):
    confirm: bool = False


class RestoreFileSelection(BaseModel):
    src: str = Field(min_length=1)
    paths: list[str] | None = Field(default=None, min_length=1)


class RestoreFilesInput(IdInput):
    file: str = Field(min_length=1)
    selections: list[RestoreFileSelection] = Field(min_length=1)
    target_config_id: str = Field(min_length=1)
    target_base_path: str = Field(min_length=1)
    exclude_patterns: list[str] = Field(default_factory=list)
    profile_id_override: str | None = None
    dry_run: bool = False
    confirm: bool = False
