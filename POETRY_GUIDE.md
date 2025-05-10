# Poetry Guide for DomainSale

This guide explains how to use Poetry with the DomainSale package, deploy it to GitHub, and install it on another host.

## Setting Up Poetry

If you don't have Poetry installed, you can install it by following the instructions on the [Poetry website](https://python-poetry.org/docs/#installation).

### Quick Installation (Linux, macOS, Windows with WSL)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Windows PowerShell

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

## Converting from setuptools to Poetry

If you've been using setuptools (setup.py), you can convert to Poetry by following these steps:

1. The `pyproject.toml` file has already been created for you.
2. You can now remove the `setup.py` file as it's no longer needed:

```bash
rm setup.py
```

3. Initialize the Poetry environment:

```bash
poetry install
```

This will create a virtual environment and install all dependencies.

## Using Poetry with DomainSale

### Installing Dependencies

```bash
poetry install
```

### Running the CLI

```bash
poetry run domainsale example.com
```

### Running Tests

```bash
poetry run pytest
```

### Activating the Virtual Environment

```bash
poetry shell
```

Then you can run commands directly:

```bash
domainsale example.com
```

### Building the Package

```bash
poetry build
```

This will create both a source distribution and a wheel in the `dist/` directory.

## Deploying to GitHub

### Creating a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in.
2. Click on the "+" icon in the top right corner and select "New repository".
3. Name your repository (e.g., "domainsale").
4. Add a description (optional).
5. Choose whether the repository should be public or private.
6. Click "Create repository".

### Initializing Git and Pushing to GitHub

Replace `yourusername` with your GitHub username:

```bash
# Initialize Git repository (if not already done)
git init

# Add all files to Git
git add .

# Commit the files
git commit -m "Initial commit"

# Add the GitHub repository as a remote
git remote add origin https://github.com/yourusername/domainsale.git

# Push to GitHub
git push -u origin main
```

Note: If your default branch is named `master` instead of `main`, use `master` in the last command.

## Publishing to PyPI (Optional)

If you want to publish your package to PyPI, you can do so with Poetry:

```bash
# Build the package
poetry build

# Publish to PyPI (you'll need to have an account)
poetry publish
```

## Installing on Another Host

### From GitHub

You can install the package directly from GitHub:

```bash
pip install git+https://github.com/yourusername/domainsale.git
```

### From PyPI (If Published)

If you've published the package to PyPI:

```bash
pip install domainsale
```

### Using Poetry

If you want to use Poetry on the other host:

```bash
# Clone the repository
git clone https://github.com/yourusername/domainsale.git

# Change to the repository directory
cd domainsale

# Install with Poetry
poetry install
```

## Development Workflow with Poetry

### Adding Dependencies

```bash
# Add a runtime dependency
poetry add some-package

# Add a development dependency
poetry add --group dev some-dev-package
```

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update a specific dependency
poetry update some-package
```

### Exporting requirements.txt (if needed)

```bash
poetry export -f requirements.txt --output requirements.txt
```

### Running Scripts

You can define custom scripts in the `pyproject.toml` file:

```toml
[tool.poetry.scripts]
domainsale = "domainsale.cli:main"
```

Then run them with:

```bash
poetry run domainsale
```

## GitHub Actions for CI/CD (Optional)

You can add GitHub Actions to automatically test and publish your package. Create a file at `.github/workflows/python-package.yml`:

```yaml
name: Python Package

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: 1.5.1
    - name: Install dependencies
      run: |
        poetry install
    - name: Lint with flake8
      run: |
        poetry run flake8 domainsale
    - name: Test with pytest
      run: |
        poetry run pytest
```

This will run tests on multiple Python versions whenever you push to the main branch or create a pull request.
