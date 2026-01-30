#!/bin/bash
# Update the Homebrew formula with the correct SHA256 for a release tarball
# Usage: ./scripts/update-formula.sh <version>
# Example: ./scripts/update-formula.sh 0.1.0

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.1.0"
    exit 1
fi

VERSION="$1"
TARBALL_URL="https://github.com/REPO_OWNER/ixargs/releases/download/v${VERSION}/ixargs-${VERSION}.tar.gz"
FORMULA="Formula/ixargs.rb"

echo "Downloading tarball to compute SHA256..."
curl -sL "$TARBALL_URL" -o /tmp/ixargs-${VERSION}.tar.gz

SHA256=$(shasum -a 256 /tmp/ixargs-${VERSION}.tar.gz | awk '{print $1}')
echo "SHA256: $SHA256"

# Update version and sha256 in formula
sed -i.bak "s|url \".*\"|url \"$TARBALL_URL\"|" "$FORMULA"
sed -i.bak "s|sha256 \".*\"|sha256 \"$SHA256\"|" "$FORMULA"

rm "${FORMULA}.bak"
rm /tmp/ixargs-${VERSION}.tar.gz

echo "Formula updated successfully!"
echo "Don't forget to replace REPO_OWNER with your GitHub username in the formula."
