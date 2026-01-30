# Maintaining ixargs Releases

This guide explains how to create releases and update the Homebrew formula.

## Release Process

### 1. Create a Release

Tag and push the release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The GitHub Actions workflow will automatically:
- Build a source distribution (`ixargs-0.1.0.tar.gz`)
- Create a GitHub release with the tarball

### 2. Update the Homebrew Formula

After the release is created, update the formula with the correct SHA256:

```bash
./scripts/update-formula.sh 0.1.0
```

This script will:
- Download the release tarball
- Calculate the SHA256 checksum
- Update the formula with the correct URL and checksum

**Important**: Don't forget to replace `REPO_OWNER` in `Formula/ixargs.rb` with your GitHub username before publishing the formula.

### 3. Update Python Dependencies (if needed)

If you've added or updated Python dependencies, you need to update the `resource` blocks in the Homebrew formula.

#### Automatic Method (Recommended)

```bash
python scripts/generate-formula-resources.py
```

This will analyze the dependencies and output resource blocks ready to paste into `Formula/ixargs.rb`.

#### Manual Method

For each dependency in `pyproject.toml`:

1. Find the package on PyPI: https://pypi.org/project/PACKAGE_NAME/
2. Download the source tarball (`.tar.gz`, not `.whl`)
3. Calculate SHA256: `shasum -a 256 PACKAGE_NAME-VERSION.tar.gz`
4. Add a resource block to the formula:

```ruby
resource "package-name" do
  url "https://files.pythonhosted.org/packages/.../package-name-X.Y.Z.tar.gz"
  sha256 "abc123..."
end
```

### 4. Test the Package Locally

Before publishing, test the package installs correctly:

```bash
# Test with pipx (recommended)
uv build --sdist
pipx install dist/ixargs-*.tar.gz
echo -e "line1\nline2\nline3" | ixargs echo
pipx uninstall ixargs
```

To test the actual Homebrew formula, you need to set up a local tap first (see `.github/QUICK_START.md` for details).

### 5. Publish to a Homebrew Tap

1. Create a GitHub repository for your tap (e.g., `homebrew-tap`)
2. Copy `Formula/ixargs.rb` to the tap repository
3. Users can install with:

```bash
brew tap YOUR_USERNAME/tap
brew install ixargs
```

## PyPI Distribution (Optional)

To also distribute via PyPI:

```bash
# Build the distribution
uv build

# Upload to PyPI (requires PyPI account and API token)
uv publish
```

Users can then install with:

```bash
pip install ixargs
# or
pipx install ixargs
```

## Version Bumping Checklist

When releasing a new version:

- [ ] Update version in `pyproject.toml`
- [ ] Commit the version change
- [ ] Create and push the git tag
- [ ] Wait for GitHub Actions to complete
- [ ] Update the Homebrew formula with `./scripts/update-formula.sh`
- [ ] Test the formula locally
- [ ] Push the updated formula to your Homebrew tap
- [ ] (Optional) Upload to PyPI
