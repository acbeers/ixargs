# Quick Start for Maintainers

## Building Locally

```bash
# Build source distribution
uv build --sdist

# Output: dist/ixargs-0.1.0.tar.gz
```

### Quick Test

Run the automated test script to build and verify everything works:

```bash
./scripts/test-build.sh
```

This will build the source distribution, install it in a test virtualenv, and verify the package works correctly.

## Testing the Build

```bash
# Install in a test environment
pip install dist/ixargs-0.1.0.tar.gz

# Or test with pipx
pipx install dist/ixargs-0.1.0.tar.gz

# Test it works
echo -e "a\nb\nc" | ixargs echo

# Uninstall
pip uninstall ixargs
# or
pipx uninstall ixargs
```

## Testing the Homebrew Formula

Homebrew requires formulae to be in a tap. For local testing:

```bash
# Build the source distribution first
uv build --sdist

# Create a local tap (one-time setup)
mkdir -p ~/homebrew-local/Formula
ln -sf "$(pwd)/Formula/ixargs.rb" ~/homebrew-local/Formula/
brew tap-new local/tap --no-git
brew tap local/tap ~/homebrew-local

# For testing, point formula to local tarball by editing Formula/ixargs.rb:
#   url "file:///path/to/ixargs/dist/ixargs-0.1.0.tar.gz"
# Then update sha256: shasum -a 256 dist/ixargs-0.1.0.tar.gz

# Install from your local tap
brew install local/tap/ixargs

# Test it works
echo "test" | ixargs echo

# Uninstall
brew uninstall ixargs
```

Alternative: test with pip/pipx instead (simpler):

```bash
uv build --sdist
pipx install dist/ixargs-*.tar.gz
echo "test" | ixargs echo
pipx uninstall ixargs
```

## Creating a Release

1. **Update version** in `pyproject.toml`

2. **Commit and tag**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git tag v0.2.0
   git push origin main v0.2.0
   ```

3. **Wait for GitHub Actions** to build and create the release

4. **Update Homebrew formula**
   ```bash
   ./scripts/update-formula.sh 0.2.0
   ```

5. **Test the package**
   ```bash
   pipx install dist/ixargs-*.tar.gz
   echo "test" | ixargs echo
   pipx uninstall ixargs
   ```

6. **Publish to your tap**
   ```bash
   cd ../homebrew-tap  # Your tap repository
   cp ../ixargs/Formula/ixargs.rb Formula/
   git add Formula/ixargs.rb
   git commit -m "ixargs: update to 0.2.0"
   git push
   ```

## Common Issues

### "python -m build" fails
Use `uv build` instead. The project uses `uv` for build tooling.

### "Formula doesn't install"
Make sure you've:
- Built the source distribution first
- Updated the `url` and `sha256` in the formula
- Replaced `REPO_OWNER` with your GitHub username

### "Dependencies are outdated"
Update the resource blocks:
```bash
python scripts/generate-formula-resources.py
```
Copy the output into `Formula/ixargs.rb`.

## See Also

- [MAINTAINING.md](../MAINTAINING.md) - Detailed maintenance guide
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guide
- [README.md](../README.md) - User documentation
