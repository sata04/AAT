# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AAT (Acceleration Analysis Tool) is a Python desktop application for analyzing microgravity experiment data. It processes acceleration data from Inner Capsule and Drag Shield sensors, calculates gravity levels, and performs statistical analysis using a PySide6 GUI with matplotlib graphs.

## Essential Commands

```bash
# Setup (using uv - recommended)
uv venv && source .venv/bin/activate    # Create and activate venv
uv pip install -e ".[dev]"               # Install with dev dependencies

# Run application
uv run python main.py                    # Normal run
AAT_DEBUG=1 uv run python main.py        # Debug mode (full logging)
uv run python main.py -v                 # Verbose mode (INFO level)

# Code quality
uv run ruff check . --fix                # Lint and auto-fix
uv run ruff format .                     # Format code
uv run pre-commit run --all-files        # Run all pre-commit hooks

# Testing
uv run pytest                            # Run all tests
uv run pytest -v                         # Verbose output
uv run pytest -m "not slow"              # Skip slow tests
uv run pytest -m gui                     # GUI tests only

# macOS app bundle
uv pip install -e ".[build]"
python scripts/build_mac_app.py          # Creates AAT.app and AAT.dmg
```

## Architecture

```
AAT/
├── main.py                          # Entry point with macOS-specific handling
├── core/                            # Core processing logic (GUI-agnostic)
│   ├── data_processor.py            # CSV loading, column detection, gravity calculation
│   ├── statistics.py                # Statistical analysis, sliding window calculations
│   ├── cache_manager.py             # Pickle + HDF5 caching system
│   ├── export.py                    # Excel and PNG export
│   ├── config.py                    # JSON configuration management
│   ├── exceptions.py                # Custom exception hierarchy
│   ├── logger.py                    # Centralized logging
│   ├── paths.py                     # Path utilities
│   └── version.py                   # Version from pyproject.toml
├── gui/                             # User interface layer
│   ├── main_window.py               # Main window and graph display
│   ├── workers.py                   # QThread workers for background processing
│   ├── settings_dialog.py           # Configuration dialog
│   ├── column_selector_dialog.py    # CSV column mapping dialog
│   ├── styles.py                    # Theme and styling
│   └── widgets.py                   # Custom widgets
└── config/
    └── config.default.json          # Default config template
```

### Key Design Patterns

**Separation of Concerns**: `core/` is GUI-agnostic and can be used independently. All heavy processing happens in `core/`, while `gui/` handles display and user interaction.

**Asynchronous Processing**: Time-intensive operations run in `QThread` workers (`gui/workers.py`). The `GQualityWorker` class is the reference implementation for background processing with progress signals.

**Intelligent Caching**: Processed data cached in `results_AAT/cache/` using pickle (DataFrames) and HDF5 (raw data). Cache invalidation triggers on: source file change, settings change, or app version change.

**Configuration**: User config stored in OS-specific directory (macOS: `~/Library/Application Support/AAT/config.json`, Windows: `%APPDATA%\AAT\config.json`, Linux: `$XDG_CONFIG_HOME/AAT/config.json`). Override with `AAT_CONFIG_DIR` env var.

### Data Processing Pipeline

1. **CSV Loading** (`data_processor.py:detect_columns`) - Auto-detect time/acceleration columns via keyword matching
2. **Synchronization** - Detect sync points in acceleration data for time alignment
3. **Gravity Calculation** - Convert acceleration to gravity units using configurable `gravity_constant`
4. **Filtering** - Extract microgravity segments based on `acceleration_threshold`
5. **Statistical Analysis** (`statistics.py`) - Sliding window min-stddev calculations
6. **G-quality Analysis** - Multi-window analysis (0.1s-1.0s range by default)
7. **Export** (`export.py`) - Excel with multiple sheets + PNG graphs

### Exception Hierarchy

All exceptions inherit from `AATException` in `core/exceptions.py`:
- `DataLoadError` / `ColumnNotFoundError` - CSV parsing issues
- `DataProcessingError` / `SyncPointNotFoundError` / `InsufficientDataError` - Processing failures
- `ConfigurationError` - Invalid settings
- `ExportError` - Output failures
- `CacheError` - Cache operations

Error messages are in Japanese for user-facing errors.

## Critical Configuration Parameters

Default values defined in `core/config.py:113-141`:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `sampling_rate` | 1000 Hz | Data frequency - affects all time calculations |
| `gravity_constant` | 9.797578 m/s² | Reference gravity for conversion |
| `acceleration_threshold` | 5.0 m/s² | Sync point detection threshold |
| `window_size` | 0.1 s | Primary analysis window |
| `g_quality_start/end/step` | 0.1/1.0/0.05 s | Multi-scale G-quality parameters |
| `invert_inner_acceleration` | true | Invert Inner Capsule data |

**Important**: When modifying processing logic, bump version in `pyproject.toml` to invalidate existing caches.

## Output Structure

Results saved in `results_AAT/` directory alongside source CSV files:
```
results_AAT/
├── <filename>.xlsx          # Multi-sheet Excel (data, statistics, G-quality)
├── cache/                   # Processing cache (*.pickle, *_raw.h5)
└── graphs/
    ├── <filename>_gl.png    # Gravity level graph
    └── <filename>_gq.png    # G-quality analysis graph
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `AAT_DEBUG=1` | Enable full debug logging |
| `AAT_LOG_LEVEL` | Set log level (DEBUG, INFO, WARNING, ERROR) |
| `AAT_CONFIG_DIR` | Override user config directory |

## Platform Notes

**macOS**: Special handling in `main.py:18-58` filters Qt/TSM warnings. Debug mode (`AAT_DEBUG=1`) disables this filtering.

**CI/CD**: GitHub Actions requires X11 libraries for headless GUI testing. Ruff is pinned to version 0.8.4.

## Testing

Test framework: pytest with pytest-qt for GUI tests. Coverage targets: 80% overall, 90% for core modules.

```bash
# Run single test file
uv run pytest tests/test_data_processor.py -v

# Run specific test
uv run pytest tests/test_data_processor.py::test_detect_columns -v
```
