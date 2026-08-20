# Secure Development

This document records the security design principles and common vulnerability classes that apply to `dbackup-mcp`. It supports project review and OpenSSF Best Practices evidence; `SECURITY.md` remains the vulnerability-reporting policy.

## Security design principles

`dbackup-mcp` applies these principles to its maintained source and public tool surface:

- **Economy of mechanism:** expose explicit typed DBackup workflows instead of a generic HTTP request tool or a second authorization system.
- **Fail-safe defaults:** reject missing or unsafe configuration, deny secret-file access unless file type and permissions satisfy the declared boundary, and require explicit confirmation for destructive operations where documented.
- **Complete mediation:** every DBackup operation is routed through the authenticated client boundary and each MCP tool applies its own validation, permission assumptions, and destructive-operation guard.
- **Open design:** security does not depend on hiding implementation details. The public repository documents the tool surface, permissions, secret-handling boundary, and compatibility assumptions.
- **Least privilege:** DBackup API keys should receive only the permissions required by the MCP workflows exposed to a consumer. The MCP does not require credential reveal, backup deletion/download, API-key administration, user/RBAC/SSO administration, or recovery-kit access.
- **Least common mechanism:** secret input is file-backed and separated from model-visible arguments; credential-profile payloads use a dedicated private directory instead of a shared generic input channel.
- **Psychological acceptability:** destructive semantics, confirmation requirements, dry-run support, and mutation classifications are explicit in the tool contract so operators can understand risk before execution.
- **Limited attack surface:** raw HTTP, credential reveal, recovery-kit download, binary backup download, backup deletion, API-key administration, user/RBAC/SSO administration, and unsupported UI-internal server actions are deliberately excluded.
- **Allowlist-oriented validation:** configuration, adapter inputs, file paths, request timeouts, enums, and supported tool operations are validated against explicit accepted forms rather than accepting arbitrary request payloads.

## Common vulnerability classes and mitigations

| Vulnerability class | Project mitigation |
|---|---|
| Credential or secret disclosure | API keys and credential payloads are file-backed; plaintext secrets are not accepted as MCP arguments; DBackup responses and error details are sanitized before model-visible output. |
| Path traversal or unsafe local file access | Secret-file inputs are constrained to the configured boundary and must satisfy private regular-file requirements; credential payloads are read only from the configured secret directory. |
| Authorization bypass / confused deputy | DBackup remains the authorization authority; the MCP exposes only curated operations and documents the minimum API-key permissions for the enabled surface. |
| Over-broad remote request capability / SSRF-style escape | No generic HTTP request tool exists. The base DBackup origin is operator configuration, and tools map only to maintained DBackup workflows. |
| Unsafe destructive operation | Destructive tools are explicitly classified and require confirmation where the tool contract specifies it; selected-file restore supports dry-run planning. |
| Injection or malformed structured input | Tool inputs are typed and validated; sensitive adapter keys are rejected; enums and bounded numeric/string inputs reject unsupported forms before API execution. |
| Sensitive error propagation | API responses and nested error details are recursively sanitized before being returned through MCP. |
| Dependency or workflow supply-chain compromise | Python dependencies are locked; GitHub Actions are full-SHA pinned; Dependabot, CodeQL, Secret Scanning, Push Protection, OpenSSF Scorecard, and release provenance provide independent review signals. |
| Compatibility drift causing unsafe behavior | DBackup `3.2.0` is the tested baseline; source-verified compatibility behavior is isolated and covered by contract tests rather than silently accepting undocumented server behavior. |

## Review expectations

Security-sensitive changes should:

1. preserve or reduce the exposed MCP and credential surface;
2. add or update regression tests when practical;
3. update `docs/tools.md`, `README.md`, or `SECURITY.md` when an externally visible security boundary changes;
4. keep production credentials and backup contents out of tests, logs, fixtures, issues, and commits;
5. pass `./scripts/verify.sh` and applicable GitHub security checks before release acceptance.

The primary maintainer must separately self-certify the OpenSSF criteria that ask whether a primary developer understands secure design principles and common vulnerability classes. This document supplies project-specific evidence but does not make that personal certification automatically.
