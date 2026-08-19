# Changelog

This file records user-visible changes to `dbackup-mcp`. Security fixes with a public CVE or equivalent identifier are called out explicitly in the release that fixes them.

## Unreleased

No user-visible changes yet.

## 0.1.0 - 2026-08-14

Initial public release.

- Added 43 typed MCP tools for curated DBackup backup administration, planning, history, adapters, verification, restore workflows, and capability/health diagnostics.
- Kept DBackup API keys and credential payloads file-backed and outside model-visible tool arguments and responses.
- Excluded raw HTTP, credential reveal, backup download/deletion, API-key administration, user/RBAC/SSO administration, and unsupported UI-internal server actions.
- Published wheel and source artifacts with `SHA256SUMS` and established DBackup `3.2.0` as the tested compatibility baseline.
