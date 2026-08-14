# Tool reference

Complete MCP tool reference for `dbackup-mcp` source package version `0.1.0`, tested against DBackup `3.2.0`.

The MCP schemas returned by the server are the authoritative input contract. This page owns the public tool inventory, mutation classification, destructive semantics and the guards that materially affect use.

## Tools

| Tool | Access | Destructive | Purpose |
|---|---|---:|---|
| `dbackup_status` | Read | No | Check DBackup health and authenticated API availability. |
| `dbackup_capabilities` | Read | No | Describe the supported DBackup contract, API boundary, and deliberate exclusions. |
| `jobs_list` | Read | No | List configured backup jobs with secret-bearing fields removed. |
| `job_get` | Read | No | Get one backup job by ID. |
| `job_plan` | Read | No | Validate and preview a complete database/directory backup job without changing DBackup. |
| `job_create` | Write | No | Create a complete database and/or directory backup job. |
| `job_update` | Write | Yes | Replace the managed configuration of an existing backup job. |
| `job_clone` | Write | No | Clone an existing backup job. |
| `job_set_enabled` | Write | No | Enable or disable an existing backup job. |
| `job_delete` | Write | Yes | Delete one backup job. Requires confirm=true. |
| `job_run` | Write | No | Start one backup job manually. |
| `history_list` | Read | No | List recent backup and restore execution history. |
| `execution_get` | Read | No | Get one execution with model-visible logs bounded to the requested tail length. |
| `execution_cancel` | Write | Yes | Cancel one running execution. Requires confirm=true. |
| `adapters_list` | Read | No | List database, storage, or notification adapters with secrets removed. |
| `adapter_get` | Read | No | Get one adapter with secrets removed. |
| `adapter_create` | Write | No | Create a database source, directory source, storage destination, or notification adapter. |
| `adapter_update` | Write | Yes | Update one adapter configuration. Secret fields are never returned. |
| `adapter_clone` | Write | No | Clone an adapter configuration. |
| `adapter_delete` | Write | Yes | Delete an unused adapter. Requires confirm=true. |
| `adapter_test` | Read | No | Test an adapter connection without persisting a new adapter. |
| `adapter_browse` | Read | No | Browse a storage SOURCE adapter path. |
| `adapter_databases` | Read | No | List databases available through a saved database source. |
| `adapter_database_stats` | Read | No | Return database sizes and table counts for a saved source. |
| `adapter_health` | Read | No | Return recent health checks for one adapter. |
| `adapter_version_history` | Read | No | Return bounded detected database-version history for one adapter. |
| `notification_logs` | Read | No | List bounded DBackup notification-delivery logs with optional filters. |
| `notification_log_get` | Read | No | Get one DBackup notification-delivery log entry. |
| `credentials_list` | Read | No | List credential profile metadata without secret payloads. |
| `credential_get` | Read | No | Get credential metadata, public key, and fingerprint without secret payloads. |
| `credential_usage` | Read | No | Show where a credential profile is referenced. |
| `credential_create_from_secret_file` | Write | No | Create a credential profile from one private JSON file inside the configured secret-input directory. Secret data is never accepted as tool input or returned. |
| `credential_update_from_secret_file` | Write | Yes | Update a credential profile from one private JSON file inside the configured secret-input directory. Secret data is never accepted as tool input or returned. |
| `credential_create_generated_ssh` | Write | No | Create an SSH credential whose private key is generated and retained by DBackup; only public metadata is returned. |
| `credential_delete` | Write | Yes | Delete an unused credential profile. Requires confirm=true. |
| `storage_history` | Read | No | Return bounded storage-usage history for one destination. |
| `storage_check_path` | Read | No | Check whether a restore target path is empty, occupied, or unverified without changing it. |
| `backups_list` | Read | No | List a bounded number of backup files for one storage destination. |
| `backup_verify` | Write | No | Verify one backup file; asynchronous verification is the default. |
| `archive_browse` | Read | No | Inspect one directory level inside a backup archive without restoring it. |
| `restore_plan` | Read | No | Analyze a backup and preview a restore request without changing data. |
| `restore_start` | Write | Yes | Start a database/directory restore. Requires confirm=true. |
| `restore_files` | Write | Yes | Restore selected files from an archive. Requires confirm=true. |

All tools publish complete MCP annotations with `openWorldHint=false`. A write tool is not automatically destructive: for example, starting a backup or verifying an archive changes DBackup state without deleting or replacing managed configuration.

## Important guards

- `job_plan` is read-only. It validates referenced database sources, selected databases, directory SOURCE adapters, source paths and DESTINATION adapters before a job is created or replaced. Directory sources default to `stop_containers=false`; explicitly enabling container stopping produces a warning.
- Adapter create/update/test inputs reject fields matching DBackup `3.2.0`'s sensitive-key contract. Credential-profile IDs are supplied through `primary_credential_id` and `ssh_credential_id` instead.
- `credential_create_from_secret_file` and `credential_update_from_secret_file` accept only a file name inside `DBACKUP_CREDENTIAL_SECRET_DIR`. The JSON payload itself is never a model-visible argument. The directory and file permissions are validated before use.
- `job_delete`, `adapter_delete`, `credential_delete` and `execution_cancel` require `confirm=true`.
- `restore_start` requires `confirm=true`.
- `restore_files` requires `confirm=true` unless `dry_run=true`, which allows target and selection validation without writing restored data.
- DBackup API responses are recursively sanitized before model-visible output is returned. Raw HTTP error bodies are not surfaced.

## DBackup API-key permissions

The complete tool surface can require these DBackup `3.2.0` permissions, depending on which workflows are invoked:

```text
jobs:read
jobs:write
jobs:execute
history:read
sources:view
sources:write
destinations:read
destinations:write
notifications:read
notifications:write
storage:read
storage:restore
credentials:read
credentials:write
credentials:delete
```

Do not grant permissions merely because they exist. This MCP does not require or expose `credentials:reveal`, `storage:download`, `storage:delete`, `sources:read`, `vault:read`, `vault:write`, user/RBAC permissions or API-key administration. A gateway or MCP client can further restrict the visible tool set.

## Credential secret files

Credential payloads that DBackup must store can be delivered as private JSON files inside `DBACKUP_CREDENTIAL_SECRET_DIR`. The file must be a regular file with mode `0600` and must be delivered by a separate secret-management mechanism. Never commit credential payload files to source control.

Generated SSH credentials are different: DBackup generates and retains the private key itself, while the MCP returns only public metadata.

## Deliberate exclusions

The server does not expose:

- raw or arbitrary HTTP requests;
- DBackup API-key administration;
- credential reveal;
- recovery-kit or master-key downloads;
- arbitrary database table-row browsing;
- public or prepared backup download URLs;
- binary backup downloads;
- backup-file deletion;
- generic system-task execution;
- DBackup user, RBAC, SSO or application administration;
- DBackup's internal Next.js server actions as an unsupported substitute for missing public REST discovery.

These are product and security boundaries, not missing raw escape hatches.

## Compatibility boundary

DBackup's bundled `3.2.0` OpenAPI specification does not fully describe its directory-job and granular file-restore model. `dbackup-mcp` therefore keeps a deliberately small `3.2.0` compatibility layer tested against the corresponding runtime routes rather than generating a broad client from OpenAPI alone.

Some objects used by DBackup's web job editor—such as retention policies, encryption profiles, naming templates, schedule presets and notification templates—are loaded through application-internal server actions instead of public API-key REST discovery. `dbackup-mcp` does not depend on those internal UI actions. A known ID may be supplied when the public job API accepts it; creating or discovering such objects remains an operator/UI bootstrap responsibility until DBackup exposes a supported REST contract for them.

DBackup `3.2.0` is the tested and supported baseline. A newer release is unverified until route/schema changes have been reviewed and the contract suite has passed for that version.
