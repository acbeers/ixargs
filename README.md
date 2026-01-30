# ixargs

**Interactive xargs** — run commands against a sequence of input arguments in a split-pane TUI.

```
some_tool | ixargs [options] cmd [args...]
```

For each line of stdin, ixargs runs `cmd` with the arguments and the line as the last argument (or replaced via `-I`). The UI shows the input list and command output side by side. Move between lines to run the command with different inputs; output supports scrolling and preserves color.

## Installation

### Homebrew (macOS)

```bash
brew tap YOUR_USERNAME/tap
brew install ixargs
```

### pip / pipx

```bash
pip install ixargs
# or for isolated install
pipx install ixargs
```

## Development Setup

### Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for environment management

### Setup

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

# Commands with option-like args (e.g. find -exec) work; use -- to separate if needed
printf 'foo\nbar\n' | uv run ixargs -I '%' find . -exec grep % {} \\;
```

## Options

| Option | Description |
|--------|-------------|
| `-z` | Split horizontally (list on left). Default. |
| `-v` | Split vertically (list on top). |
| `-t` | Trim leading and trailing whitespace from each input line. |
| `-I replstr` | Replace `replstr` in the args with each stdin line instead of appending it. |

After ixargs options, the first remaining argument is the command; everything after is passed as arguments to it. Commands with option-like args (e.g. `find -exec`) work naturally. Use `--` to explicitly separate ixargs options from the command when the command itself starts with `-`.

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

### Homebrew (Recommended for macOS)

1. Copy [Formula/ixargs.rb](Formula/ixargs.rb) into a Homebrew tap (e.g. your own repo or fork).
2. Replace `REPO_OWNER` in the formula with your GitHub username or org.
3. After the first release, update the `sha256` checksum in the formula (run `shasum -a 256` on the downloaded tarball).
4. Users can then tap and install:

   ```bash
   brew tap YOUR_USERNAME/ixargs
   brew install ixargs
   ```

The Homebrew formula installs ixargs in an isolated Python virtualenv and symlinks the binary to your PATH.

### PyPI (All platforms)

Install directly with pip or pipx:

```bash
pip install ixargs
# or with pipx for isolated install
pipx install ixargs
```

### Creating a release

Tag a release to build the source distribution and create a GitHub release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The [release workflow](.github/workflows/release.yml) builds a source distribution tarball and uploads it to the GitHub release. The same tarball is used by both Homebrew and PyPI.

### Local Testing

To test building the source distribution locally:

```bash
uv build --sdist
# Output will be in dist/ixargs-VERSION.tar.gz
```

## License

MIT
