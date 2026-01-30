# Contributing to ixargs

Thank you for your interest in contributing to ixargs!

## Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/ixargs.git
cd ixargs
```

2. **Install dependencies with uv**

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
```

3. **Run ixargs in development**

```bash
# Run with uv
echo -e "line1\nline2\nline3" | uv run ixargs echo

# Or install in editable mode
pip install -e .
echo -e "line1\nline2\nline3" | ixargs echo
```

## Project Structure

```
ixargs/
├── ixargs/           # Main package
│   ├── __init__.py
│   ├── __main__.py   # Entry point for python -m ixargs
│   ├── app.py        # Textual app and UI
│   ├── app.css       # Textual CSS styles
│   ├── cli.py        # CLI argument parsing
│   └── runner.py     # Command execution logic
├── Formula/          # Homebrew formula
│   └── ixargs.rb
├── scripts/          # Maintenance scripts
│   ├── update-formula.sh
│   └── generate-formula-resources.py
└── pyproject.toml    # Project metadata and dependencies
```

## Making Changes

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Keep functions focused and well-documented

### Testing Changes

Test your changes manually:

```bash
# Test basic functionality
echo -e "a\nb\nc" | uv run ixargs echo

# Test with a real command
ls | uv run ixargs wc -l

# Test placeholder replacement
echo -e "foo\nbar" | uv run ixargs -I {} echo "File: {}"

# Test vertical split
echo -e "1\n2\n3" | uv run ixargs -v seq
```

### Adding Dependencies

1. Add the dependency to `pyproject.toml`:

```toml
dependencies = [
    "textual>=7.4.0",
    "new-package>=1.0.0",
]
```

2. Sync the environment:

```bash
uv sync
```

3. Update the Homebrew formula resources:

```bash
python scripts/generate-formula-resources.py
```

4. Copy the output resource blocks into `Formula/ixargs.rb`

## Submitting Changes

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes and commit**

```bash
git add .
git commit -m "Add feature: your feature description"
```

3. **Push and create a pull request**

```bash
git push origin feature/your-feature-name
```

## Release Process

See [MAINTAINING.md](MAINTAINING.md) for detailed release instructions.

## Questions or Issues?

- Open an issue on GitHub
- Check existing issues for similar questions
- Read the README and MAINTAINING docs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
