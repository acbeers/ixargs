# ixargs

**Interactive xargs** — run commands against a sequence of input arguments in a split-pane TUI.

```
some_tool | ixargs [options] cmd [args...]
```

For each line of stdin, ixargs runs `cmd` with the arguments and the line as the last argument (or replaced via `-I`). The UI shows the input list and command output side by side. Move between lines to run the command with different inputs; output supports scrolling and preserves color.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for environment management

## Setup

```bash
uv sync
```

## Usage

```bash
# Basic: run `echo` for each line
printf 'a\nb\nc\n' | uv run ixargs echo

# Horizontal split (list left, output right) — default
ls | uv run ixargs -z wc -l

# Vertical split (list top, output bottom)
ls | uv run ixargs -v head -5

# Replace placeholder in args instead of appending
printf 'foo\nbar\n' | uv run ixargs -I '{}' echo "file: {}"
```

## Options

| Option | Description |
|--------|-------------|
| `-z` | Split horizontally (list on left). Default. |
| `-v` | Split vertically (list on top). |
| `-I replstr` | Replace `replstr` in the args with each stdin line instead of appending it. |

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `j` / `↓` | Next line |
| `k` / `↑` | Previous line |
| `Space` | Next page |
| `b` | Previous page |
| `<` | Top of output |
| `>` | Bottom of output |
| `q` | Quit |
| `?` | Help |
| `/` | Search (stub) |
| `n` / `N` | Search next / previous |

## Distribution

### Binaries (GitHub Releases)

Tag a release to build packaged binaries and create a GitHub release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The [release workflow](.github/workflows/release.yml) builds with PyInstaller (onedir) on macOS (arm64) and Linux (x86_64), then uploads tarballs to the release. Download `ixargs-<version>-darwin-arm64.tar.gz` or `ixargs-<version>-linux-x86_64.tar.gz`, extract (you get an `ixargs/` directory), and run `./ixargs/ixargs`.

### Homebrew (macOS, Apple Silicon)

1. Copy [Formula/ixargs.rb](Formula/ixargs.rb) into a Homebrew tap (e.g. your own repo or fork).
2. Replace `REPO_OWNER` in the formula with your GitHub username or org.
3. After the first release, set the real `sha256` (run `shasum -a 256` on the downloaded tarball).
4. Users can then tap and install:

   ```bash
   brew tap YOUR_USERNAME/ixargs
   brew install ixargs
   ```

Intel Macs have no pre-built binary; use `pip install ixargs` or build from source.

### Local PyInstaller build

```bash
uv sync --extra dev
pyinstaller ixargs.spec
# onedir output: dist/ixargs/ (run dist/ixargs/ixargs)
```

## License

MIT
