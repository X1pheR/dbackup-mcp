# dbackup-mcp

A typed Model Context Protocol server for safe administration of [DBackup](https://github.com/Skyfay/DBackup) through its authenticated API.

This community project is not affiliated with or endorsed by the DBackup project. DBackup itself is licensed under GPL-3.0; `dbackup-mcp` is a separate integration project licensed under MIT.

## Design

`dbackup-mcp` maps backup administration workflows to explicit MCP tools instead of exposing a generic HTTP request primitive. The server keeps DBackup API keys and credential payloads outside model-visible arguments, validates inputs before requests are sent, recursively removes secret-bearing response fields, and publishes MCP read/destructive annotations.

The current source targets DBackup `3.2.0`. Most operations use DBackup's public REST contract. Directory-source and granular-restore behavior that is present in DBackup `3.2.0` but incomplete in its bundled OpenAPI description is implemented against the corresponding versioned application routes and covered by contract tests.

## Coverage

Version `0.1.0` exposes 43 curated tools.

| Area | Coverage | Notes |
|---|---|---|
| Service contract | Supported | Health plus a capabilities tool that reports the supported DBackup version, API boundary, required API-key permissions and deliberate exclusions. |
| Jobs | Broad | List, get, plan, create, replace/update, clone, enable/disable, delete and manual run. Database and directory sources can be combined. |
| Execution and history | Broad | Execution history, execution detail, cancellation and notification-delivery logs. |
| Adapters | Broad | List/get/create/update/clone/delete, connection test, directory browse, database discovery/stats, health and database-version history. |
| Credentials | Safe management subset | Metadata, usage, generated SSH credentials and create/update through private local secret files. Credential reveal is excluded. |
| Storage and restore | Broad safe subset | Backup listing, verification, storage history, archive browsing, restore analysis, restore-target preflight, full restore and selected-file restore. Binary download and backup deletion are excluded. |
| Templates and encryption profiles | Reference-only | Jobs can carry known IDs, but DBackup `3.2.0` does not expose public API-key REST discovery for every retention, naming, schedule, notification, exclude-pattern or encryption-profile object used by its web UI. |
| Authentication and application administration | Excluded | API-key management, users, RBAC, SSO, recovery-kit operations and generic system tasks remain outside this MCP. |

### Tool surface

#### Service and jobs

- `dbackup_status`
- `dbackup_capabilities`
- `jobs_list`
- `job_get`
- `job_plan`
- `job_create`
- `job_update`
- `job_clone`
- `job_set_enabled`
- `job_delete`
- `job_run`

`job_plan` performs read-only validation of referenced database sources, selected databases, directory SOURCE adapters, source paths and DESTINATION adapters. Directory sources default to `stop_containers=false`; explicitly enabling container stopping produces a warning. Deployment-specific backup-selection policy belongs to the operator or MCP consumer and is not hardcoded into this generic server.

#### Execution and notifications

- `history_list`
- `execution_get`
- `execution_cancel`
- `notification_logs`
- `notification_log_get`

#### Adapters

- `adapters_list`
- `adapter_get`
- `adapter_create`
- `adapter_update`
- `adapter_clone`
- `adapter_delete`
- `adapter_test`
- `adapter_browse`
- `adapter_databases`
- `adapter_database_stats`
- `adapter_health`
- `adapter_version_history`

Adapter configuration can contain non-secret structural values such as host, port, path, bucket or region. Fields matching DBackup `3.2.0`'s sensitive-key contract are rejected from MCP adapter inputs. DBackup credential-profile IDs are supplied through `primary_credential_id` and `ssh_credential_id` instead.

#### Credentials

- `credentials_list`
- `credential_get`
- `credential_usage`
- `credential_create_from_secret_file`
- `credential_update_from_secret_file`
- `credential_create_generated_ssh`
- `credential_delete`

Generated SSH credentials are created inside DBackup; the private key is retained by DBackup. Other credential payloads can be imported from a private JSON file inside `DBACKUP_CREDENTIAL_SECRET_DIR`. The file name, not its content, is supplied as an MCP argument.

Example credential input file:

```json
{"username":"backup","password":"replace-with-a-real-secret"}
```

The file must be delivered by a separate secret-management mechanism, must be a regular file with mode `0600`, and must never be committed to source control.

#### Storage and restore

- `backups_list`
- `backup_verify`
- `storage_history`
- `archive_browse`
- `restore_plan`
- `storage_check_path`
- `restore_start`
- `restore_files`

Restore mutations require `confirm=true`. Granular file restore also supports DBackup's dry-run path so selections and target paths can be checked without writing restored data.

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

## Requirements

- Python `3.12+`
- DBackup `3.2.0`, or a compatible release whose used routes retain the same contract
- a DBackup API key with only the permissions required by the enabled MCP workflows
- an MCP client or gateway that supports STDIO servers
- `uv` for the documented source workflow

## DBackup API-key permissions

The complete 43-tool surface can require the following DBackup `3.2.0` permissions, depending on which tools are actually invoked:

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

Do not grant permissions merely because they exist. In particular, this MCP does not require or expose `credentials:reveal`, `storage:download`, `storage:delete`, `sources:read`, `vault:read`, `vault:write`, user/RBAC permissions or API-key administration.

A gateway or MCP client can further restrict the visible tool set. A read-oriented consumer should not receive mutation tools just because the DBackup API key is capable of them.

## Configuration

| Variable | Required | Default | Meaning |
|---|---:|---|---|
| `DBACKUP_BASE_URL` | yes | - | DBackup HTTP(S) origin without `/api`, for example `https://backup.example.com`. |
| `DBACKUP_API_KEY_FILE` | yes | - | Private regular file containing one DBackup API key. Group/other permissions are rejected. |
| `DBACKUP_CREDENTIAL_SECRET_DIR` | no | - | Private directory containing mode-`0600` JSON credential payload files used only by explicit credential create/update tools. |
| `DBACKUP_REQUEST_TIMEOUT_SECONDS` | no | `15` | Per-request timeout in seconds, greater than zero and at most 120. |

Example MCP registration from an installed package:

```json
{
  "mcpServers": {
    "dbackup": {
      "command": "dbackup-mcp",
      "env": {
        "DBACKUP_BASE_URL": "https://backup.example.com",
        "DBACKUP_API_KEY_FILE": "/run/secrets/dbackup-api-key",
        "DBACKUP_CREDENTIAL_SECRET_DIR": "/run/secrets/dbackup-credentials"
      }
    }
  }
}
```

The credential directory is optional. Omit it when the MCP should not import or update DBackup credential profiles from local files.

## Running from source

The repository includes `uv.lock` for a reproducible source environment.

```bash
uv sync --frozen --extra test
DBACKUP_BASE_URL=https://backup.example.com \
DBACKUP_API_KEY_FILE=/run/secrets/dbackup-api-key \
uv run --frozen dbackup-mcp
```

A gateway can launch the checkout directly:

```json
{
  "command": "uv",
  "args": ["run", "--frozen", "--directory", "/path/to/dbackup-mcp", "dbackup-mcp"],
  "env": {
    "DBACKUP_BASE_URL": "https://backup.example.com",
    "DBACKUP_API_KEY_FILE": "/run/secrets/dbackup-api-key"
  }
}
```

## Security model

- API keys and credential payloads are file-backed and never accepted as MCP plaintext arguments.
- API-key and credential files must be regular files with no group or other permissions; the credential directory must also be private.
- Adapter MCP inputs reject DBackup `3.2.0` sensitive configuration keys and use credential-profile references instead.
- DBackup API responses are recursively sanitized before model-visible output is returned.
- HTTP error bodies are reduced to sanitized DBackup error/message text; raw response bodies are not surfaced.
- No generic request escape hatch exists.
- Delete, cancel and restore operations require explicit confirmation where appropriate and publish destructive MCP annotations.
- All tools publish complete MCP annotations with `openWorldHint=false`.
- The DBackup API key remains the authorization boundary; the MCP server does not invent a second RBAC system.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and the maintained security boundary.

## Compatibility

DBackup's bundled `3.2.0` OpenAPI specification does not fully describe its directory-job and granular file-restore model. This project therefore keeps a deliberately small `3.2.0` compatibility layer tested against the corresponding runtime routes rather than generating a broad client from OpenAPI alone.

Some objects used by DBackup's web job editor—such as retention policies, encryption profiles, naming templates, schedule presets and notification templates—are loaded through application-internal server actions instead of public API-key REST discovery. `dbackup-mcp` does not depend on those internal UI actions. A known ID may be supplied when the public job API accepts it; creating or discovering such objects remains an operator/UI bootstrap responsibility until DBackup exposes a supported REST contract for them.

A newer DBackup release can therefore be compatible without being automatically supported. Review route/schema changes and rerun the contract suite before expanding the declared compatibility range.

## Development and verification

Run the repository-local verification entry point:

```bash
./scripts/verify.sh
```

It installs the locked test environment, runs the complete test suite and builds source/wheel artifacts into a temporary directory. GitHub Actions uses the same entry point.

Dependency version updates are configured through Dependabot for both `uv` and GitHub Actions. GitHub-native dependency, secret and code scanning are repository settings rather than application features; their required publication state is documented in the project release workflow.

## Release lifecycle

Normal development validates source but does not publish a release. Accepted version tags are separate release gates. Before the first public release, the repository source, relevant Git history, dependency state, security scans, public metadata and fresh-checkout workflow must all pass public-readiness review.

## License

MIT. See [LICENSE](LICENSE).
