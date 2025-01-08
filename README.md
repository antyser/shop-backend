# Shop Backend

A Python backend service using FastAPI.

## Development Setup

### Prerequisites

1. Install [uv](https://github.com/astral-sh/uv):
   ```bash
   # macOS
   brew install uv
   
   # Linux/macOS (alternative)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Project Setup

1. Create virtual environment for ide
   ```bash
   uv venv
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

### Running Scripts

All Python scripts should be run using `uv run` prefix:

```bash

# Run tests
uv run pytest

# Run specific script
uv run python path/to/script.py
```

### Project Structure
```
shop-backend/
├── .venv/             # Virtual environment
├── pyproject.toml     # Project configuration and dependencies
└── src/               # Source code
    └── shop_backend/  # Main package directory
```

## Troubleshooting

### Virtual Environment Issues

If you need to recreate the virtual environment:
```bash
rm -rf .venv
uv venv
uv sync
```

## Development Guidelines

Use pre-commit hooks for code quality:
   ```bash
   # Install pre-commit hooks
   source .venv/bin/activate
   pre-commit install
   
   # Run pre-commit hooks manually
   pre-commit run --all-files
   ```

It includes

- **Black**: Code formatter that ensures consistent code style
- **Ruff**: Fast Python linter that combines multiple tools
- **Mypy**: Static type checker for Python

These tools are automatically run on each commit through pre-commit hooks. You can also run them manually:

```bash
# Format code with Black
uv run black .

# Lint with Ruff
uv run ruff check .
uv run ruff check . --fix  # Auto-fix issues

# Type check with Mypy
uv run mypy .
```