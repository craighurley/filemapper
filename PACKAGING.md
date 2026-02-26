# Packaging Guide

This document describes how to build and distribute the FileMapper package.

## Prerequisites

- Python 3.13+

## Setup

Install the necessary pip packages:

```shell
pip install -Ue ".[dev]"
```

## Building the package

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
task validate-local-package
```

This will:

1. Create a venv
2. Install the local package into the venv
3. Attempt running the application
4. Remove the venv

## Publishing to PyPI

### PyPI Requirements

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

Now validate that package can be installed from test.pypi.org:

```shell
task validate-pypi-package
```

This will:

1. Create a venv
2. Install the package from test.pypi.org into the venv
3. Attempt running the application
4. Remove the venv

### Production PyPI

Once verified on test PyPI, deploy to production PyPi:

```shell
task deploy-prod
```

## Entry Point

The package creates a command-line tool that users can run after installation:

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

## Troubleshooting

### Build fails with "No module named build"

```shell
task install
```

### Upload fails with authentication error

Ensure you have a `~/.pypirc` file with valid API tokens:

### Package doesn't include expected files

Check `pyproject.toml` - the `[tool.setuptools.packages.find]` and `[tool.setuptools]` sections control what gets included.

## Tasks

```sh
task build                       # Build distribution package
task check-version               # Check version matches git tag in pyproject.toml
task clean                       # Clean build artefacts and cache files
task deploy-prod                 # Deploy package to pypi.org
task deploy-test                 # Deploy package to test.pypi.org
task install                     # Install dependencies
task lint                        # Format and then lint
task test                        # Run tests
task validate-local-package      # Use the local package to install into a clean venv for validation testing
task validate-pypi-package       # Install the package from test.pypi.org into a clean venv for validation testing
```
