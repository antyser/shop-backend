# Shop Backend

A Python backend service using FastAPI.

## Development Setup

### Prerequisites

1. Install [pyenv](https://github.com/pyenv/pyenv#installation):
   ```bash
   # macOS
   brew install pyenv
   
   # Linux
   curl https://pyenv.run | bash
   ```

2. Install [uv](https://github.com/astral-sh/uv):
   ```bash
   # macOS
   brew install uv
   
   # Linux/macOS (alternative)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Add to your shell configuration (~/.bashrc, ~/.zshrc, etc.):
   ```bash
   # pyenv configuration
   export PYENV_ROOT="$HOME/.pyenv"
   [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
   eval "$(pyenv init -)"
   ```

### Project Setup

1. Install Python 3.12.5:
   ```bash
   pyenv install 3.12.5
   ```

2. Set Python version for the project:
   ```bash
   pyenv local 3.12.5
   ```

3. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

4. Install dependencies:
   ```bash
   # Install all dependencies (including dev)
   uv pip install -e ".[dev]"
   
   # Install only production dependencies
   uv pip install -e .
   ```

### Common Commands

- Activate virtual environment:
  ```bash
  source .venv/bin/activate  # On Unix/macOS
  # or
  .venv\Scripts\activate  # On Windows
  ```

- Add new dependencies:
  ```bash
  # Add to pyproject.toml manually, then:
  uv pip install -e .
  ```

- Add development dependencies:
  ```bash
  # Add to pyproject.toml under [project.optional-dependencies].dev, then:
  uv pip install -e ".[dev]"
  ```

- Update dependencies:
  ```bash
  uv pip install --upgrade -e ".[dev]"
  ```

- Show installed packages:
  ```bash
  uv pip list
  ```

### Project Structure
```
shop-backend/
├── .python-version     # Created by pyenv (contains: 3.12.5)
├── .venv/             # Virtual environment
├── pyproject.toml     # Project configuration and dependencies
└── src/               # Source code
    └── shop_backend/  # Main package directory
```

## Troubleshooting

### Pyenv Issues

If Python version is not being recognized:
```bash
pyenv rehash
```

If pyenv commands are not found, ensure your shell configuration is correct:
```bash
# Add to ~/.bashrc or ~/.zshrc
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

### Virtual Environment Issues

If you need to recreate the virtual environment:
```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Python Version Issues

If Python version isn't updating after pyenv local:
```bash
exec "$SHELL"  # Restart your shell
```

## Development Guidelines

1. Always activate the virtual environment before working
2. Keep `pyproject.toml` in version control
3. Update dependencies by modifying `pyproject.toml` and running `uv pip install -e ".[dev]"`
4. Keep Python version consistent across team members using pyenv
5. Use pre-commit hooks for code quality:
   ```bash
   # Install pre-commit hooks
   source .venv/bin/activate
   pre-commit install
   
   # Run pre-commit hooks manually
   pre-commit run --all-files
   ```

### Code Quality Tools

The project uses several tools to maintain code quality:

- **Black**: Code formatter that ensures consistent code style
- **Ruff**: Fast Python linter that combines multiple tools
- **Mypy**: Static type checker for Python

These tools are automatically run on each commit through pre-commit hooks. You can also run them manually:

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .
ruff check . --fix  # Auto-fix issues

# Type check with Mypy
mypy .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
