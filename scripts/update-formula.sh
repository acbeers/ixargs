#!/bin/bash
# Update the Homebrew formula with the correct SHA256 for a release tarball
# Usage: ./scripts/update-formula.sh <version> [repo_owner]
# Example: ./scripts/update-formula.sh 0.1.0

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version> [repo_owner]"
    echo "Example: $0 0.1.0"
    exit 1
fi

VERSION="$1"
REPO_OWNER="${2:-}"
FORMULA="Formula/ixargs.rb"

if [ -z "$REPO_OWNER" ]; then
    # Try to infer from git remote, falling back to REPO_OWNER placeholder.
    if command -v git >/dev/null 2>&1; then
        ORIGIN_URL="$(git remote get-url origin 2>/dev/null || true)"
        # Supports:
        # - git@github.com:OWNER/ixargs.git
        # - https://github.com/OWNER/ixargs.git
        REPO_OWNER="$(echo "$ORIGIN_URL" | sed -nE 's#(git@github.com:|https://github.com/)([^/]+)/ixargs(\.git)?#\2#p')"
    fi
fi

if [ -z "$REPO_OWNER" ]; then
    REPO_OWNER="REPO_OWNER"
fi

TARBALL_URL="https://github.com/${REPO_OWNER}/ixargs/releases/download/v${VERSION}/ixargs-${VERSION}.tar.gz"

echo "Downloading tarball to compute SHA256..."
TMP_TARBALL="/tmp/ixargs-${VERSION}.tar.gz"
curl -fsSL "$TARBALL_URL" -o "$TMP_TARBALL"

# Fail early if we downloaded an HTML error page instead of a .tar.gz
python3 - "$TMP_TARBALL" <<'PY'
import gzip
import sys

path = sys.argv[1]
try:
    with gzip.open(path, "rb") as f:
        f.read(1)
except Exception as e:
    raise SystemExit(f"Downloaded file is not a valid .tar.gz: {path}\n{e}")
PY

SHA256=$(shasum -a 256 "$TMP_TARBALL" | awk '{print $1}')
echo "SHA256: $SHA256"

# Update ONLY the top-level url/sha256 (do NOT clobber resource blocks)
python3 - "$FORMULA" "$TARBALL_URL" "$SHA256" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

formula_path = Path(sys.argv[1])
new_url = sys.argv[2]
new_sha = sys.argv[3]

lines = formula_path.read_text(encoding="utf-8").splitlines(keepends=True)

resource_idx = next((i for i, l in enumerate(lines) if l.startswith("  resource ")), len(lines))

url_idx = next((i for i, l in enumerate(lines[:resource_idx]) if l.startswith("  url ")), None)
sha_idx = next((i for i, l in enumerate(lines[:resource_idx]) if l.startswith("  sha256 ")), None)

if url_idx is None or sha_idx is None:
    raise SystemExit("Could not find top-level 'url'/'sha256' lines in formula (before first resource).")

lines[url_idx] = f'  url "{new_url}"\n'
lines[sha_idx] = f'  sha256 "{new_sha}"\n'

formula_path.write_text("".join(lines), encoding="utf-8")
PY

rm "$TMP_TARBALL"

echo "Formula updated successfully!"
if [ "$REPO_OWNER" = "REPO_OWNER" ]; then
    echo "NOTE: REPO_OWNER is still a placeholder; update it in Formula/ixargs.rb"
fi
