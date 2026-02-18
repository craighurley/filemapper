# FileMapper Packaging Guide

This document describes how to build and distribute the FileMapper package.

## Prerequisites

Install Taskfile <https://taskfile.dev/docs/installation>.

Then install the necessary pip packages:

```shell
task install
```

## Building the Package

Build both source distribution (`.tar.gz`) and wheel (`.whl`):

```shell
task build
```

This will:

1. Clean any previous build artefacts
2. Build the package using `python -m build`
3. Create files in `dist/`:
   - `filemapper-X.Y.Z.tar.gz` (source distribution)
   - `filemapper-X.Y.Z-py3-none-any.whl` (wheel)

## Testing the package

Install the locally built package:

```shell
task validate-package-local
```

This will:

1. Create a venv
2. Install the local package into the venv
3. Attempt running the application
4. Remove the venv

Install the package from pypi:

```shell
task validate-package-pypi
```

This will:

1. Create a venv
2. Install the package from test.pypi.org into the venv
3. Attempt running the application
4. Remove the venv

## Publishing to PyPI

### Requirements

You'll need PyPI credentials configured. Set up authentication with:

```shell
# Create ~/.pypirc with your API tokens
[pypi]
username = __token__
password = pypi-...

[testpypi]
username = __token__
password = pypi-...
```

### Test PyPI (recommended first)

Deploy to test PyPI to verify everything works:

```shell
task deploy-test
```

This will:

1. Build the package
2. Deploy to test.pypi.org

### Production PyPI

Once verified on test PyPI, deploy to production:

Deploy to test PyPI to verify everything works:

```shell
task deploy-test
```

## Entry Point

The package creates a `filemapper` command-line tool that users can run after installation:

```shell
filemapper -i input.csv -c config.yaml -o output.csv
```

This is configured in `pyproject.toml`:

```toml
[project.scripts]
filemapper = "filemapper:main"
```

## Version Management

Update the version in `pyproject.toml`:

```toml
[project]
version = "X.Y.Z"
```

Follow semantic versioning:

- **Major** (X): Breaking changes
- **Minor** (Y): New features, backwards-compatible
- **Patch** (Z): Bug fixes, backwards-compatible

## Dependencies

**Core dependencies** (required to run):

- `python-dateutil>=2.8.2`
- `PyYAML>=6.0.1`

**Dev dependencies** (optional):

- `pytest>=7.4.0`
- `pytest-cov>=4.1.0`
- `ruff>=0.15.1`
- `yamllint`

**Deploy dependencies** (for publishing):

- `build>=1.0.0`
- `setuptools>=68.0`
- `twine>=4.0.0`
- `wheel>=0.42.0`

## Troubleshooting

### Build fails with "No module named build"

```shell
task install
```

### Upload fails with authentication error

Ensure you have a `~/.pypirc` file with valid API tokens:

### Package doesn't include expected files

Check `pyproject.toml` - the `[tool.setuptools.packages.find]` and `[tool.setuptools]` sections control what gets included.
