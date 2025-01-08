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

2. Install [Poetry](https://python-poetry.org/docs/#installation):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Add to your shell configuration (~/.bashrc, ~/.zshrc, etc.):
   ```bash
   # pyenv configuration
   export PYENV_ROOT="$HOME/.pyenv"
   [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
   eval "$(pyenv init -)"
   
   # poetry configuration (if not automatically added)
   export PATH="$HOME/.local/bin:$PATH"
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

3. Configure Poetry to create virtual environment in project directory:
   ```bash
   poetry config virtualenvs.in-project true
   ```

4. Initialize Poetry project (skip if pyproject.toml exists):
   ```bash
   poetry init
   ```

5. Install dependencies:
   ```bash
   poetry install
   ```

### Common Commands

- Activate virtual environment:
  ```bash
  poetry shell
  ```

- Add new dependencies:
  ```bash
  poetry add package-name
  ```

- Add development dependencies:
  ```bash
  poetry add --group dev package-name
  ```

- Update dependencies:
  ```bash
  poetry update
  ```

- Show installed packages:
  ```bash
  poetry show
  ```

- Run a command in virtual environment:
  ```bash
  poetry run python your_script.py
  ```

### Project Structure
```
shop-backend/
├── .python-version     # Created by pyenv (contains: 3.12.5)
├── .venv/             # Virtual environment (created by Poetry)
├── pyproject.toml     # Poetry project configuration and dependencies
├── poetry.lock        # Lock file for dependencies
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

### Poetry Issues

If you need to recreate the virtual environment:
```bash
poetry env remove python
poetry install
```

To debug Poetry environment:
```bash
poetry env info
poetry debug info
```

### Python Version Issues

If Python version isn't updating after pyenv local:
```bash
exec "$SHELL"  # Restart your shell
```

## Development Guidelines

1. Always use `poetry shell` or `poetry run` to run commands
2. Keep `pyproject.toml` and `poetry.lock` in version control
3. Update dependencies through Poetry commands only
4. Keep Python version consistent across team members using pyenv

## License

This project is licensed under the MIT License - see the LICENSE file for details.
