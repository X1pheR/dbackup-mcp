# dbackup-mcp

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/X1pheR/dbackup-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/X1pheR/dbackup-mcp)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14174/badge)](https://www.bestpractices.dev/projects/14174)
[![Verified by M8ven](https://m8ven.ai/badge/mcp/x1pher-dbackup-mcp-1ppp3e?variant=verified)](https://m8ven.ai/mcp/x1pher-dbackup-mcp-1ppp3e)

A typed Model Context Protocol server for curated backup administration of [DBackup](https://github.com/Skyfay/DBackup) through its authenticated API.

This community project is not affiliated with or endorsed by the DBackup project. DBackup is licensed under GPL-3.0; `dbackup-mcp` is a separate integration project licensed under MIT.

## What it covers

`dbackup-mcp` exposes explicit MCP workflows instead of a generic HTTP escape hatch. The current source package version is `0.1.0` and exposes 43 curated tools across:

- backup jobs and executions;
- storage, database, directory, and notification adapters;
- backup discovery, details, logs, verification, and downloads;
- credentials with secret-safe mutation paths;
- schedules, retention policies, naming templates, exclude presets, and container policies;
- tags, notifications, metrics, health, audit access, and application settings;
- bounded restore planning, dry-run validation, full restores, selected database restores, and selected file restores.

See [`docs/tools.md`](docs/tools.md) for the complete tool catalog and mutation policy.

## Deliberate exclusions

The MCP intentionally does **not** expose:

- arbitrary raw HTTP requests;
- credential reveal or private-key retrieval;
- direct backup deletion;
- generic backup download tools;
- API-key administration;
- user, RBAC, SSO, or session administration;
- unsupported UI-internal server actions.

These boundaries are part of the public MCP contract rather than temporary omissions.

## Requirements

- Python 3.12+
- a reachable DBackup instance
- a DBackup API key stored in a private file
- DBackup 3.2.0 is the tested compatibility baseline

## Installation

Clone the repository and install with `uv`:

```bash
git clone https://github.com/X1pheR/dbackup-mcp.git
cd dbackup-mcp
uv sync --frozen
```

For development and tests:

```bash
uv sync --frozen --extra test
```

## Configuration

The server uses file-backed secrets rather than accepting secret values through MCP arguments.

Required environment variables:

```text
DBACKUP_BASE_URL=https://backup.example.com
DBACKUP_API_KEY_FILE=/run/secrets/dbackup_api_key
```

Optional environment variables:

```text
DBACKUP_REQUEST_TIMEOUT_SECONDS=15
DBACKUP_CREDENTIAL_SECRET_DIR=/run/secrets/dbackup-credentials
```

`DBACKUP_API_KEY_FILE` must point to a private regular file. Group/other permissions are rejected. `DBACKUP_CREDENTIAL_SECRET_DIR` is only needed for the explicit credential create/update tools and must contain private mode-0600 JSON payload files.

## Running

Run the MCP server over stdio:

```bash
uv run dbackup-mcp
```

The package also exposes the Python module entry point:

```bash
uv run python -m dbackup_mcp
```

## Permissions and least privilege

DBackup API permissions still govern what the server can do. The MCP does not bypass DBackup authorization.

Use a dedicated API key with only the permissions required for the workflows you intend to expose. Treat the API key as a privileged operational credential because many DBackup administration operations are inherently high impact.

## Security behavior

The MCP applies an explicit security boundary around DBackup:

- API keys are loaded from private files and never accepted through tool arguments;
- credential secret payloads are loaded only from an explicitly configured private directory;
- sensitive adapter keys are rejected rather than forwarded;
- model-visible responses and errors are sanitized;
- no generic request tool exists;
- destructive operations require explicit confirmation;
- restore workflows support planning and dry-run validation before execution;
- MCP tool metadata keeps `openWorldHint=false`.

Report vulnerabilities privately through GitHub's security reporting flow. See [`SECURITY.md`](SECURITY.md).

See [Secure Development](docs/SECURE-DEVELOPMENT.md) for the project-specific secure-design model and common vulnerability mitigations.

## Compatibility boundary

This repository intentionally targets a tested DBackup baseline rather than claiming compatibility with every upstream release. The current baseline is DBackup 3.2.0.

When DBackup changes its API, update the compatibility evidence and tests before claiming support for the newer version.

## Development

Run the repository verification suite with:

```bash
./scripts/verify.sh
```

That command installs the locked test environment, compiles the package, runs the full test suite, builds the wheel and source distribution, and verifies the generated artifacts.

Repository maintenance also includes:

- Dependabot for GitHub Actions and Python dependencies;
- CodeQL analysis for Python and Actions;
- OpenSSF Scorecard analysis;
- secret scanning and push protection;
- signed GitHub/Sigstore provenance for future release artifacts.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution expectations and [`CHANGELOG.md`](CHANGELOG.md) for release history.

## License

MIT. See [`LICENSE`](LICENSE).
