# Migration Guide: PyInstaller to Virtualenv Distribution

This guide helps you transition from the PyInstaller binary distribution to the new virtualenv-style Homebrew formula.

## What Changed?

### Before (PyInstaller)
- Platform-specific compiled binaries (darwin-arm64, linux-x86_64)
- Large release artifacts (~30-50 MB per platform)
- PyInstaller `.spec` file for builds
- Separate binary for each platform
- GitHub Actions built binaries on multiple runners

### After (Virtualenv)
- Single source distribution for all platforms
- Smaller release artifacts (~50 KB)
- Standard Python packaging with `pyproject.toml`
- Homebrew installs in an isolated virtualenv
- GitHub Actions builds one source tarball

## Benefits of the New Approach

1. **Simpler maintenance**: One source distribution instead of multiple binaries
2. **Smaller releases**: Source tarballs are much smaller than compiled binaries
3. **Better compatibility**: Works with standard Python tooling (pip, pipx, poetry, etc.)
4. **Faster CI**: Single build job instead of matrix of platforms
5. **More flexible**: Users can install with their preferred Python package manager
6. **Standard Homebrew patterns**: Uses the same virtualenv approach as most Python formulae

## For Users

### If you installed via Homebrew (old way)

The new formula is incompatible with the old one. Uninstall the old version first:

```bash
# Uninstall old version
brew uninstall ixargs

# Remove old tap if you added one
brew untap OLD_TAP_NAME

# Install new version
brew tap YOUR_USERNAME/tap
brew install ixargs
```

### If you downloaded binaries directly

You can now install via Homebrew or pip instead:

```bash
# Option 1: Homebrew (macOS)
brew tap YOUR_USERNAME/tap
brew install ixargs

# Option 2: pip (all platforms)
pip install ixargs

# Option 3: pipx (isolated install)
pipx install ixargs
```

## For Maintainers

### Files Removed
- `ixargs.spec` - PyInstaller specification file
- `.github/workflows/release.yml` - Old workflow (replaced with simpler version)
- Platform-specific build configurations

### Files Added
- `scripts/update-formula.sh` - Helper to update formula after releases
- `scripts/generate-formula-resources.py` - Generate Homebrew resource blocks
- `MAINTAINING.md` - Detailed release and maintenance guide
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - Development guide

### Files Modified
- `Formula/ixargs.rb` - Now uses `Language::Python::Virtualenv`
- `pyproject.toml` - Removed PyInstaller from dev dependencies
- `README.md` - Updated installation and distribution sections
- `.gitignore` - Removed PyInstaller-specific entries
- `.github/workflows/release.yml` - Simplified to build source distribution only

### New Release Process

1. **Tag and push**
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

2. **Update formula**
   ```bash
   ./scripts/update-formula.sh 0.2.0
   ```

3. **Test locally**
   ```bash
   pipx install dist/ixargs-*.tar.gz
   echo "test" | ixargs echo
   pipx uninstall ixargs
   ```

4. **Push to tap**
   ```bash
   cd ../homebrew-tap
   cp ../ixargs/Formula/ixargs.rb Formula/
   git add Formula/ixargs.rb
   git commit -m "ixargs: update to 0.2.0"
   git push
   ```

See [MAINTAINING.md](MAINTAINING.md) for complete release instructions.

## Troubleshooting

### "Formula doesn't work on my platform"

The new formula uses `Language::Python::Virtualenv`, which works on all platforms Homebrew supports. If you encounter issues:

1. Ensure you have Python 3.13+ available
2. Try installing with pip/pipx instead: `pipx install ixargs`
3. Report the issue with your platform details

### "Dependencies are out of date"

Update the formula resources:

```bash
python scripts/generate-formula-resources.py
```

Then copy the output into `Formula/ixargs.rb`.

### "GitHub Actions workflow fails"

The new workflow is much simpler. Common issues:

- **Build fails**: Ensure `pyproject.toml` is valid and all files are committed
- **Upload fails**: Check GitHub token permissions (needs `contents: write`)
- **Wrong filename**: Workflow expects `ixargs-VERSION.tar.gz` format

## Questions?

Open an issue on GitHub if you have questions about the migration.
