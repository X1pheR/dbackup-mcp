# dbackup-mcp

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/X1pheR/dbackup-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/X1pheR/dbackup-mcp)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14174/badge)](https://www.bestpractices.dev/projects/14174)

A typed Model Context Protocol server for curated backup administration of [DBackup](https://github.com/Skyfay/DBackup) through its authenticated API.

This community project is not affiliated with or endorsed by the DBackup project. DBackup is licensed under GPL-3.0; `dbackup-mcp` is a separate integration project licensed under MIT.

## What it covers

`dbackup-mcp` exposes explicit MCP workflows instead of a generic HTTP escape hatch. The current source package version is `0.1.0` and exposes 43 curated tools across:

- backup jobs and read-only job planning;
- execution history, cancellation and notification logs;
- database, storage and notification adapters;
- credential-profile references without credential reveal;
- backup inspection, verification and bounded restore workflows;
- capability and health diagnostics.

The server deliberately excludes raw HTTP, credential reveal, backup download/deletion, API-key administration, user/RBAC/SSO administration and unsupported DBackup UI-internal server actions.

See the complete [Tool reference](docs/tools.md) for every tool, mutation classification, destructive semantics, permissions and important guards.

## Feedback and contributions

Use [GitHub Issues](https://github.com/X1pheR/dbackup-mcp/issues) for bug reports and feature requests and pull requests for proposed changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, test requirements, and change expectations. Security issues must follow the private process in [SECURITY.md](SECURITY.md).

User-visible release changes are summarized in [CHANGELOG.md](CHANGELOG.md).

## Requirements

- Python `3.12+`
- DBackup `3.2.0` as the tested and supported baseline; other versions are unverified unless explicitly documented
- a DBackup API key with only the permissions required by the enabled MCP workflows
- an MCP client or gateway that supports STDIO servers
- `uv` for the documented source workflow

## Configuration

| Variable | Required | Default | Meaning |
| --- | --- | --- | --- |
| `DBACKUP_URL` | yes | — | DBackup base URL |
| `DBACKUP_API_KEY_FILE` | preferred | — | File containing the API key |
| `DBACKUP_API_KEY` | fallback | — | API key value when file-backed configuration is not available |
| `DBACKUP_TIMEOUT_SECONDS` | no | `15` | API request timeout |
| `DBACKUP_VERIFY_TLS` | no | `true` | Verify TLS certificates |
| `DBACKUP_MUTATIONS_ENABLED` | no | `false` | Enable mutation tools |
| `DBACKUP_SECRET_INPUT_DIR` | only for secret-file credential tools | — | Private directory containing credential input JSON files |

File-backed API-key configuration is preferred because it keeps the key out of process arguments and normal configuration output.

Example:

```bash
export DBACKUP_URL="https://dbackup.example.net"
export DBACKUP_API_KEY_FILE="/run/secrets/dbackup-api-key"
export DBACKUP_MUTATIONS_ENABLED="false"
```

### Permissions

Use a dedicated DBackup API key with the smallest permissions required for the enabled workflows. Read-only deployments do not need mutation permissions. Mutation-capable deployments should grant only the specific DBackup permissions required by the selected tools rather than broad administrative access.

## Running from source

```bash
git clone https://github.com/X1pheR/dbackup-mcp.git
cd dbackup-mcp
uv sync --frozen --extra test
uv run dbackup-mcp
```

For a normal MCP client, configure the command to run `uv run dbackup-mcp` from the repository directory and provide the required environment variables or mounted secret files.

## Docker

Build the image locally:

```bash
docker build -t dbackup-mcp:local .
```

Example STDIO launch:

```bash
docker run --rm -i \
  -e DBACKUP_URL="https://dbackup.example.net" \
  -e DBACKUP_API_KEY_FILE="/run/secrets/dbackup-api-key" \
  -v /private/dbackup-api-key:/run/secrets/dbackup-api-key:ro \
  dbackup-mcp:local
```

If credential mutation tools are required, mount a separate private directory and set `DBACKUP_SECRET_INPUT_DIR`. The server accepts only regular files from that directory and does not return secret values through MCP responses.

## Security model

The server keeps the exposed boundary intentionally small:

- all tools are explicit and typed; no generic request forwarding is exposed;
- API keys can be loaded from private files and are never returned by tools;
- adapter responses remove configured sensitive fields before they cross the MCP boundary;
- client-visible API errors are sanitized;
- destructive operations require explicit confirmation;
- selected restore workflows support dry-run planning before execution;
- file-backed credential mutations resolve secret data server-side from a private directory;
- tool annotations use `openWorldHint=false` because calls are constrained to the configured DBackup instance.

See [SECURITY.md](SECURITY.md) for private vulnerability reporting and supported-version policy. See [Secure Development](docs/SECURE-DEVELOPMENT.md) for the project-specific secure-design model and common vulnerability mitigations.

## Compatibility

The tested compatibility baseline is DBackup `3.2.0`.

The server intentionally does not expose endpoints or fields that were observed only in the web UI without a stable supported API contract. A future DBackup release may therefore require a compatibility review before the baseline is moved.

Compatibility changes should include:

1. review of the DBackup release notes and API behavior;
2. targeted adapter/client tests for changed endpoints or schemas;
3. a full `./scripts/verify.sh` run;
4. README/tool-reference updates when the supported boundary changes.

## Development

Install the test dependency set and run the complete repository verification:

```bash
./scripts/verify.sh
```

The verification script performs:

- frozen dependency synchronization;
- Python compilation checks;
- the full pytest suite;
- wheel and source-distribution builds;
- artifact verification.

Changes should preserve the explicit MCP boundary and add or update tests where practical. See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete contributor workflow.

## Dependency and supply-chain maintenance

- dependencies are locked in `uv.lock`;
- Dependabot monitors Python and GitHub Actions dependencies;
- CodeQL analyzes Python and workflow code;
- OpenSSF Scorecard runs on the repository;
- release builds use GitHub Actions and generate Sigstore-backed GitHub artifact attestations/provenance for release artifacts.

## License

`dbackup-mcp` is released under the [MIT License](LICENSE).
