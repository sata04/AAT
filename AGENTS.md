# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: Application entry point (PyQt6 GUI).
- `core/`: Core logic (data loading, statistics, export, logging, config, exceptions).
- `gui/`: UI layer (main window, workers, dialogs).
- `config/`: `config.default.json` template. User-specific `config.json` is optional and git-ignored.
- `docs/`: Developer and testing guides. Tests are not present yet; when adding, create `tests/` (pytest is configured to look there).
- Outputs: written under `results_AAT/` (graphs, Excel, caches). Do not commit.

## Build, Test, and Development Commands
- Create env: `uv venv && source .venv/bin/activate`
- Install (dev): `uv pip install -e ".[dev]"`
- Run app: `uv run python main.py` (env vars: `AAT_DEBUG=1`, `AAT_LOG_LEVEL=INFO`).
- Lint/format: `uv run ruff check . --fix` and `uv run ruff format .`
- Tests: if adding tests, first `mkdir -p tests` then run `uv run pytest -v --cov=core --cov=gui`.
- Pre-commit: `uv run pre-commit install && uv run pre-commit run --all-files`

## Coding Style & Naming Conventions
- Python ≥ 3.9. Line length 120, spaces for indent, double quotes (ruff formatter).
- Imports sorted by ruff (isort rules). Keep `core`/`gui` as first-party.
- Names: modules/files `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`.
- Prefer small, pure functions in `core/`; keep GUI side-effects in `gui/`.

## Testing Guidelines
- Status: no tests in repo yet. Pytest is configured to use `tests/`.
- Framework: pytest (+ pytest-qt for GUI) via `[tool.pytest.ini_options]`.
- Layout: create `tests/`; name files `test_*.py` or `*_test.py`, classes `Test*`, functions `test_*`.
- Marks: use `@pytest.mark.gui` for Qt tests, `@pytest.mark.slow` for long runs.
- Focus: prioritize `core/` coverage; use signals/behavior assertions for GUI.

## Commit & Pull Request Guidelines
- Use Conventional Commits: e.g., `feat:`, `fix:`, `chore:`, `chore(release): 9.3.0`.
- PRs: clear description, linked issues, reproduction steps; include before/after screenshots for GUI changes.
- Checklist: ruff clean, formatted, tests pass locally, no artifacts committed (`results_AAT/`, caches, `config.json`).

## Security & Configuration Tips
- Do not commit secrets or user-specific settings; copy `config/config.default.json` to `config.json` locally if needed.
- Prefer relative paths; large data should be outside the repo or git-ignored.
