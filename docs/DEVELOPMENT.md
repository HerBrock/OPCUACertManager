# Developer Guide

## Project Structure

```text
OPCUACertManager/
├── src/                    # Main source code
│   ├── core/               # Business logic without tkinter dependencies
│   ├── ui/                 # Graphical user interface (tkinter)
│   └── utils/              # Utility modules
├── tests/                  # Unit and integration tests
├── docs/                   # Documentation
└── ...                     # Project configuration files
```

## How to Contribute

### 1. Create a Branch

```bash
git checkout -b feature/new-functionality
# or for bug fixes
git checkout -b fix/ui-bug-fix
```

### 2. Develop and Test

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
```

### 3. Update the Documentation

- `CHANGELOG.md`: Add an entry to the `[Unreleased]` section.
- `docs/`: Update the documentation when making architectural or UI changes.

### 4. Update the Version

Follow Semantic Versioning (SemVer):

```python
# src/__version__.py
__version__ = "0.2.0"  # Minor: new functionality
# or
__version__ = "0.1.1"  # Patch: bug fix
# or
__version__ = "1.0.0"  # Major: stable release
```

```toml
# pyproject.toml
version = "0.2.0"
```

### 5. Commit the Changes

```bash
git add src/__version__.py pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
```

### 6. Push and Create Tags

```bash
git tag -a v0.2.0 -m "Version 0.2.0"
git push origin feature/new-functionality --tags
```

## Commit Conventions

The project follows [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Description | Example |
|------|-------------|---------|
| `feat:` | New functionality | `feat: add certificate viewer` |
| `fix:` | Bug fix | `fix: StringVar not updating after Browse` |
| `docs:` | Documentation changes | `docs: update ARCHITECTURE.md` |
| `style:` | Formatting without logic changes | `style: format code with black` |
| `refactor:` | Code restructuring | `refactor: separate UI from core logic` |
| `test:` | Tests | `test: add unit tests for ca.py` |
| `chore:` | Maintenance tasks | `chore: bump version to 0.2.0` |

### Commit Message Examples

```bash
# Good commits
git commit -m "feat: add batch certificate generation"
git commit -m "fix: enforce CA immutability when loading a project"
git commit -m "refactor: extract the menu bar into a separate module"

# Poor commits
git commit -m "fix stuff"
git commit -m "updated code"
git commit -m "changes"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_core/test_ca.py -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

```python
# tests/test_core/test_ca.py
import pytest
from pathlib import Path
from src.core.ca import create_ca


def test_create_ca_success(tmp_path):
    """Test CA creation with default parameters."""
    result = create_ca(
        ca_folder=tmp_path / "ca",
        common_name="Test CA",
    )

    assert result["success"] is True
    assert Path(result["ca_cert_path"]).exists()
    assert Path(result["ca_key_path"]).exists()
```

## Coding Style

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Use [type hints](https://docs.python.org/3/library/typing.html).
- Write docstrings in English using Google or Sphinx style.

```python
def create_ca(
    ca_folder: str | Path = "certs/ca",
    key_size: int = 2048,
    country_name: str = "ES",
) -> dict:
    """
    Create and save a complete Certificate Authority.

    Args:
        ca_folder: Folder path where CA files will be saved.
        key_size: RSA key size in bits.
        country_name: Country code.

    Returns:
        A dictionary containing the success status and file paths.
    """
    ...
```

### Automatic Formatting

```bash
# Format the code with Black
black src/ tests/

# Run Ruff linting
ruff check src/ tests/
```

## Dependencies

### Installing Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies
pip install -e ".[dev]"
```

### Adding a New Dependency

1. Add it to `pyproject.toml`:

```toml
[project]
dependencies = [
    "cryptography>=41.0.0",
    "new-library>=1.0.0",
]
```

2. Update `requirements.txt`:

```bash
pip freeze > requirements.txt
```

3. Create a commit:

```bash
git commit -m "chore: add new-library dependency"
```

## Debugging

### Logging

```python
from src.utils.logger import default_logger

logger = default_logger


def my_function():
    logger.info("Starting process...")
    try:
        ...
        logger.success("Process completed")
    except Exception as error:
        logger.error(f"Error: {error}", exc_info=True)
```

### Debugger

```bash
# Visual Studio or VS Code: press F5 to start debugging
# Python pdb
import pdb; pdb.set_trace()

# Or, with Python 3.7+
breakpoint()
```

## Release Process

### Release Checklist

- [ ] All tests pass.
- [ ] Documentation is up to date.
- [ ] `CHANGELOG.md` is up to date.
- [ ] The version is updated in `__version__.py` and `pyproject.toml`.
- [ ] No `*_key.pem` files are tracked by Git.
- [ ] Code review is complete.

### Release Commands

```bash
# 1. Update the version
# Edit src/__version__.py and pyproject.toml

# 2. Update the changelog
# Edit CHANGELOG.md

# 3. Commit the changes
git add src/__version__.py pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"

# 4. Create a tag
git tag -a v0.2.0 -m "Version 0.2.0 - New features"

# 5. Push the release
git push origin main --tags
```

## Troubleshooting

### Common Problems

**Error: `ModuleNotFoundError: No module named 'src.core'`**

Solution: Make sure that `src/__init__.py` exists and that the import path is correct.

**Error: `StringVar not updating`**

Solution: Explicitly call `variable.set(value)` instead of assigning the value directly.

**Error: `CA files not found`**

Solution: Verify that `has_valid_ca()` returns `True` before generating certificates.

## Resources

- [Python Documentation](https://docs.python.org/3/)
- [Cryptography Documentation](https://cryptography.io/)
- [tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [OPC UA Foundation](https://opcfoundation.org/)
