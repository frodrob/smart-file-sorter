#!/usr/bin/env bash
# Idempotent environment bootstrap for smart-file-sorter.
# Safe to run repeatedly: it refreshes dependencies without rewriting lockfiles.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- System dependency: python venv support (needed to create .venv) ---
if ! dpkg -s python3.12-venv >/dev/null 2>&1; then
  echo "==> Installing python3.12-venv"
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3.12-venv
fi

# --- Backend: Python virtual environment + editable install ---
echo "==> Setting up backend"
cd "$REPO_ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
./.venv/bin/pip install --upgrade pip --quiet
./.venv/bin/pip install -e ".[dev]" --quiet

# --- Frontend: node dependencies ---
echo "==> Setting up frontend"
cd "$REPO_ROOT/frontend"
npm install --no-fund --no-audit

echo "==> Setup complete"
