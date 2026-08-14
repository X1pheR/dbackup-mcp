#!/usr/bin/env bash
set -euo pipefail

command -v uv >/dev/null 2>&1 || {
  echo "uv is required to verify this repository" >&2
  exit 1
}

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

uv sync --frozen --extra test
PYTHONPYCACHEPREFIX="$work_dir/pycache" uv run --frozen --extra test python -m compileall -q src tests
uv run --frozen --extra test pytest -p no:cacheprovider
uv build --out-dir "$work_dir/build"

test -n "$(find "$work_dir/build" -maxdepth 1 -type f -name '*.whl' -print -quit)"
test -n "$(find "$work_dir/build" -maxdepth 1 -type f -name '*.tar.gz' -print -quit)"
