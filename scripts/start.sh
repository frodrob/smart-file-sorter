#!/usr/bin/env bash
# Per-boot reconciliation: guarantee runtime dependencies exist before the
# backend/frontend terminals launch.
#
# When an agent boots from a prebuilt environment build, the `install` step is
# skipped and the baked snapshot is trusted. If that snapshot does not contain
# the Python venv / node_modules for the current checkout, the dev servers would
# fail to start. This script repairs that case. It is a fast no-op whenever the
# dependencies are already present, so normal boots are not slowed down.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

needs_setup=0
if [ ! -x "$REPO_ROOT/backend/.venv/bin/python" ]; then
  echo "==> backend/.venv missing"
  needs_setup=1
fi
if [ ! -d "$REPO_ROOT/frontend/node_modules" ]; then
  echo "==> frontend/node_modules missing"
  needs_setup=1
fi

if [ "$needs_setup" -eq 1 ]; then
  echo "==> Dependencies incomplete; running scripts/setup.sh"
  bash "$REPO_ROOT/scripts/setup.sh"
else
  echo "==> Dependencies already present; nothing to do"
fi
