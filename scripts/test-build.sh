#!/bin/bash
# Test the complete build and installation workflow
# Usage: ./scripts/test-build.sh

set -e

echo "=== Testing ixargs build and installation ==="
echo

# Clean up any previous builds
echo "1. Cleaning previous builds..."
rm -rf dist/ build/
echo "   ✓ Clean"
echo

# Build source distribution
echo "2. Building source distribution..."
uv build --sdist
TARBALL=$(ls dist/ixargs-*.tar.gz)
echo "   ✓ Built: $TARBALL"
echo

# Check tarball size
SIZE=$(ls -lh "$TARBALL" | awk '{print $5}')
echo "3. Tarball size: $SIZE"
echo

# List tarball contents
echo "4. Tarball contents (first 20 files):"
tar -tzf "$TARBALL" | head -20
echo "   ..."
echo

# Test installation in a temporary virtual environment
echo "5. Testing installation in virtualenv..."
TEMP_VENV=$(mktemp -d)
python3 -m venv "$TEMP_VENV"
source "$TEMP_VENV/bin/activate"

pip install --quiet "$TARBALL"
echo "   ✓ Installed"
echo

# Test that ixargs command exists
echo "6. Testing ixargs command..."
which ixargs
echo "   ✓ Command found"
echo

# Test basic functionality
echo "7. Testing that ixargs binary works..."
# Check version info is accessible via Python import
python -c "import ixargs; print(f'   ✓ Version: {ixargs.__version__}')"
echo

# Clean up
deactivate
rm -rf "$TEMP_VENV"
echo "8. Cleanup complete"
echo

echo "=== All tests passed! ==="
echo
echo "The source distribution is ready at: $TARBALL"
echo "You can now:"
echo "  - Test with pipx: pipx install $TARBALL"
echo "  - Create a release: git tag v0.x.0 && git push origin v0.x.0"
echo "  - Update formula: ./scripts/update-formula.sh 0.x.0"
