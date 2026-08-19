# Security policy

## Supported versions

The latest maintained release line is the supported public baseline unless a release note says otherwise. Security fixes are developed on `main` and released through the normal versioned release lifecycle.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability, leaked credential or secret-handling defect.

Use [GitHub private vulnerability reporting](https://github.com/X1pheR/dbackup-mcp/security/advisories/new) for this repository. If that channel is unexpectedly unavailable, contact the repository owner through the GitHub profile and request a private reporting channel without including exploit details or secret values in a public message.

Useful reports include:

- the affected `dbackup-mcp` version or commit;
- the compatible DBackup version;
- the affected MCP tool or configuration boundary;
- reproducible steps using non-secret test data;
- expected versus observed behavior;
- impact and any known safe workaround.

Never send real API keys, passwords, private keys, access tokens or production backup contents in a vulnerability report.

## Security boundary

`dbackup-mcp` is designed to keep credential material outside model-visible tool arguments and responses:

- the DBackup API key is read from a private local file;
- credential create/update payloads are read only from private JSON files under one configured directory;
- adapter inputs reject DBackup-sensitive configuration keys;
- DBackup responses are recursively sanitized before MCP output;
- raw HTTP, credential reveal, recovery-kit download, binary backup download, backup deletion, API-key administration and user/RBAC/SSO administration are not exposed;
- destructive tools require explicit confirmation where appropriate;
- DBackup's own API-key permissions remain the underlying authorization boundary.

A security issue includes any path that allows a caller to bypass these boundaries, disclose a secret, escape the configured credential directory, invoke an undocumented raw request, or perform a destructive operation without the declared guard.

## Dependency and code security

The repository uses locked Python dependencies, full-SHA-pinned GitHub Actions, repository-local verification, GitHub Actions CI, Dependabot and OpenSSF Scorecard. Public-release acceptance also requires applicable GitHub-native dependency alerts, secret scanning with push protection and CodeQL code scanning to be reviewed and green before a release is published.

These scanners supplement rather than replace source/history review and the project test suite.
