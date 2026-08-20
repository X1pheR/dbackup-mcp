# dbackup-mcp

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/X1pheR/dbackup-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/X1pheR/dbackup-mcp)

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
|---|---:|---|---|
| `DBACKUP_BASE_URL` | yes | - | DBackup HTTP(S) origin without `/api`, for example `https://backup.example.com`. |
| `DBACKUP_API_KEY_FILE` | yes | - | Private regular file containing one DBackup API key. Group/other permissions are rejected. |
| `DBACKUP_CREDENTIAL_SECRET_DIR` | no | - | Private directory containing mode-`0600` JSON credential payload files for explicit credential create/update tools. |
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

Omit `DBACKUP_CREDENTIAL_SECRET_DIR` when the MCP should not create or update DBackup credential profiles from local secret files.

## Running from source

The repository includes `uv.lock` for a reproducible source environment.

```bash
uv sync --frozen --extra test
DBACKUP_BASE_URL=https://backup.example.com \
DBACKUP_API_KEY_FILE=/run/secrets/dbackup-api-key \
uv run --frozen dbackup-mcp
```

A gateway can also launch the checkout with `uv run --frozen --directory /path/to/dbackup-mcp dbackup-mcp` and the same environment variables.

## Permissions

DBackup remains the authorization boundary. Grant only the permissions required by the workflows exposed to a given MCP consumer; a gateway can further restrict the visible tool set.

The full 43-tool surface can require job, history, source, destination, notification, storage/restore and credential-reference permissions. It does **not** require credential reveal, backup download/delete, API-key administration, user/RBAC/SSO administration or recovery-kit access. See the [Tool reference](docs/tools.md#dbackup-api-key-permissions) for the exact full-surface permission set.

## Security

- API keys and credential payloads are file-backed and are never accepted as plaintext MCP arguments.
- Secret input files must be private regular files; adapter inputs reject DBackup-sensitive configuration keys and use credential-profile references instead.
- DBackup responses and error details are sanitized before model-visible output is returned.
- No generic request escape hatch exists.
- Destructive tools are explicitly annotated and confirmation is enforced where required; selected-file restore supports a dry-run path.
- All tools publish `openWorldHint=false`.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and the maintained security boundary. See [Secure Development](docs/SECURE-DEVELOPMENT.md) for the project-specific secure-design model and common vulnerability mitigations.

## Compatibility

DBackup `3.2.0` is the tested and supported baseline. The bundled OpenAPI description does not fully cover directory-job and granular file-restore behavior, so this project keeps a small source-verified `3.2.0` compatibility layer covered by contract tests.

Some objects used by DBackup's web job editor are available only through application-internal server actions rather than public API-key REST discovery. `dbackup-mcp` does not depend on those internal UI actions; known IDs may be supplied where the public job API accepts them. See the [Tool reference](docs/tools.md#compatibility-boundary) for details.

## Development and release

Run the repository-local verification entry point:

```bash
./scripts/verify.sh
```

GitHub Actions uses the same verification path. Dependabot maintains the locked dependency set and pinned workflow dependencies within accepted compatibility ranges. OpenSSF Scorecard runs on `main` and weekly and publishes its public result for independent repository-security review.

Normal development does not publish a release. An accepted strict SemVer tag (`vMAJOR.MINOR.PATCH`) triggers the release workflow, which fails closed while the repository is private, verifies the exact tag/source/package version, reruns verification, proves two independent wheel/source builds are byte-identical, generates signed GitHub/Sigstore build provenance for the release artifacts, creates a draft release, attaches artifacts plus `SHA256SUMS` and the provenance bundle, and only then publishes the release. It does not publish to PyPI.

## License

MIT. See [LICENSE](LICENSE).
