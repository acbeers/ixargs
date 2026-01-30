# Changelog

All notable changes to ixargs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Breaking**: Switched from PyInstaller binary distribution to virtualenv-style Homebrew formula
- Distribution now uses Python source packages instead of compiled binaries
- Simplified release process - single source distribution works for all platforms
- Build system uses `uv build` instead of `python -m build`

### Removed
- PyInstaller build system and `.spec` file
- Platform-specific binary releases (darwin-arm64, linux-x86_64)
- `dev` optional dependency group in `pyproject.toml`

### Added
- Homebrew formula with virtualenv installation using `Language::Python::Virtualenv`
- Helper scripts for maintaining releases:
  - `scripts/update-formula.sh` - Update formula after releases
  - `scripts/generate-formula-resources.py` - Generate Homebrew resource blocks
  - `scripts/test-build.sh` - Test build and installation workflow
- Comprehensive documentation:
  - `MAINTAINING.md` - Release and maintenance guide
  - `CONTRIBUTING.md` - Development guide
  - `MIGRATION.md` - Migration guide from PyInstaller
  - `.github/QUICK_START.md` - Quick reference for maintainers
  - `CHANGELOG.md` - Version history

## [0.1.0] - Initial Release

### Added
- Interactive TUI for running commands against stdin lines
- Split-pane interface (horizontal and vertical layouts)
- Keyboard navigation (vim-style and arrow keys)
- Command placeholder support with `-I` option
- Input line trimming with `-t` option
- Textual-based terminal UI with rich text support
- Color-preserving command output
