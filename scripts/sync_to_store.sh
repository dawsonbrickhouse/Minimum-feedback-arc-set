#!/usr/bin/env bash
# Copy the working tree (without the virtualenv/caches) and a git bundle of the
# full history to the Project store.
set -euo pipefail
STORE="${1:-/cursor/stores/bc-01a185a8-05be-73f8-adc3-447ee1195470/docs}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$STORE/fas-platform"
rsync -r --inplace --delete --exclude .git --exclude .venv --exclude __pycache__ --exclude .pytest_cache \
  --exclude '*.egg-info' --exclude results/scratch "$ROOT/" "$STORE/fas-platform/"
git -C "$ROOT" bundle create "$STORE/fas-platform.bundle" --all
echo "synced to $STORE/fas-platform and $STORE/fas-platform.bundle"
