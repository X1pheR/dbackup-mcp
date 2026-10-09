# Changelog

This file records user-visible changes to `dbackup-mcp`. Security fixes with a public CVE or equivalent identifier are called out explicitly in the release that fixes them.

## Unreleased

- Added public OpenSSF Scorecard reporting and protected-branch repository controls.
- Future releases publish signed GitHub/Sigstore build provenance alongside checksums and reproducible package artifacts.
- Added explicit contribution and private vulnerability-reporting routes.

## 0.2.1 - 2026-10-09

- Added optional `refresh=true` to `backups_list` to bypass DBackup's storage-list cache for real-time storage enumeration using existing protected API credentials.
- Kept the default cached behavior and bounded maximum results; no standalone SMB client or new credential path.
- Added request-shape and model-default regression tests.

## 0.2.0 - 2026-09-29

- Added `execution_wait_terminal`, a bounded read-only waiter for existing backup and restore executions with explicit timeout and bounded log output.
- Kept terminal waiting idempotent: it issues only execution-read requests and never starts, replays, cancels or modifies work.
- Raised the tested DBackup compatibility baseline to `3.4.0` after current source/runtime verification and live contract acceptance.

## 0.1.0 - 2026-08-14

Initial public release.

- Added 43 typed MCP tools for curated DBackup backup administration, planning, history, adapters, verification, restore workflows, and capability/health diagnostics.
- Kept DBackup API keys and credential payloads file-backed and outside model-visible tool arguments and responses.
- Excluded raw HTTP, credential reveal, backup download/deletion, API-key administration, user/RBAC/SSO administration, and unsupported UI-internal server actions.
- Published wheel and source artifacts with `SHA256SUMS` and established DBackup `3.2.0` as the tested compatibility baseline.
