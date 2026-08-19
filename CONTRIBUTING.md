# Contributing

Contributions are welcome through GitHub issues and pull requests.

## Before opening a change

- Use GitHub Issues for reproducible bugs and feature proposals.
- Use the private reporting process in [SECURITY.md](SECURITY.md) for suspected vulnerabilities or secret-handling defects.
- Keep a pull request focused on one coherent change and avoid unrelated formatting or dependency churn.
- Never include production API keys, backup contents, private endpoints, credential payloads, or other secret material in issues, fixtures, tests, logs, or commits.

## Development setup

The supported development baseline is Python 3.12 with the repository lock file:

```bash
uv sync --frozen --extra test
```

Run the same verification entry point used by CI before submitting a pull request:

```bash
./scripts/verify.sh
```

## Change requirements

- Add or update automated tests for new behavior and bug fixes where a regression test is practical.
- Preserve the typed, bounded MCP surface; do not add a generic HTTP or credential-reveal escape hatch.
- Update `docs/tools.md` when a tool, mutation classification, permission requirement, guard, or externally visible input/output contract changes.
- Update README or security documentation when requirements, compatibility, configuration, or trust boundaries change.
- Add a concise entry under `Unreleased` in [CHANGELOG.md](CHANGELOG.md) for user-visible changes.
- Keep dependency changes within the declared compatibility bounds unless the pull request explicitly owns a compatibility change.

A pull request is ready for review when repository verification passes and its documentation/tests describe the behavior it changes.
