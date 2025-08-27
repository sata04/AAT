# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AAT (Acceleration Analysis Tool) v9.3.0 is a Python desktop application for analyzing experimental data in microgravity environments. It processes acceleration data from Inner Capsule and Drag Shield sensors, calculates gravity levels, and performs statistical analysis to evaluate microgravity quality using a PyQt6 GUI with interactive graphing capabilities.

## Essential Commands

### Development and Testing
```bash
# Environment setup with uv (recommended)
uv venv                              # Create virtual environment
source .venv/bin/activate            # Activate on macOS/Linux
# or
.venv\Scripts\activate               # Activate on Windows

# Install dependencies with uv
uv pip install -e .                  # Install as editable package
uv pip install -e ".[dev]"           # Install with dev dependencies
uv pip sync                          # Sync dependencies from pyproject.toml

# Alternative: Direct pip installation (if not using uv)
pip install -e .                     # Install as editable package
pip install -e ".[dev]"              # Install with dev dependencies

# Run the application
uv run python main.py                # Run with uv (auto-activates venv)
# or
python main.py                       # Run directly (requires activated venv)

# Run with debug output (shows all logs)
AAT_DEBUG=1 uv run python main.py

# Run with verbose output (shows INFO level logs)
uv run python main.py --verbose
# or
uv run python main.py -v

# Set custom log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
AAT_LOG_LEVEL=INFO uv run python main.py

# Run tests with uv (when implemented)
uv run pytest                        # Run all tests
uv run pytest -v                     # Verbose output
uv run pytest -m "not slow"          # Skip slow tests
uv run pytest -m gui                 # Run GUI tests only
uv run pytest --cov=core --cov=gui   # With coverage report

# Code quality and formatting with uv
uv run ruff check .                  # Lint all files
uv run ruff check . --fix            # Lint and auto-fix issues
uv run ruff format .                 # Format all files
uv run ruff check . --diff          # Show what would be changed

# Pre-commit hooks (with uv)
uv run pre-commit install            # Install hooks
uv run pre-commit run --all-files    # Run all checks manually
```

### Package Management
The project uses `pyproject.toml` for dependency management with **uv** as the recommended package manager:
- **Package Manager**: uv (fast Python package installer and resolver)
- Core dependencies: PyQt6, matplotlib, numpy, pandas, openpyxl, tables
- Dev dependencies: ruff, pytest, pytest-cov, pytest-qt, pytest-mock
- Python requirement: >=3.9

**uv benefits**:
- Fast dependency resolution and installation
- Automatic virtual environment management
- Compatible with `pyproject.toml` and pip requirements
- Integrated tool running with `uv run` command

## Interactive Features

### Graph Interaction
- **Mouse Drag Selection**: Click and drag on graphs to select time ranges for detailed analysis
- **Real-time Statistics**: Selected range statistics update instantly in the status bar
- **Zoom and Pan**: Interactive navigation of large datasets
- **Auto-ranging**: Graphs automatically adjust to data bounds

## Architecture Overview

### Project Structure
```
AAT/
├── main.py                          # Application entry point with macOS-specific handling
├── config.json                      # Runtime configuration (user-specific)
├── config/
│   └── config.default.json          # Default configuration template
├── pyproject.toml                   # Modern Python packaging and dependencies
├── .pre-commit-config.yaml          # Code quality automation
├── core/                            # Core processing logic (GUI-agnostic)
│   ├── data_processor.py            # CSV loading, column detection, gravity calculation
│   ├── statistics.py                # Statistical analysis and sliding window calculations
│   ├── cache_manager.py             # Intelligent data caching system (pickle + HDF5)
│   ├── export.py                    # Excel and graph export functionality
│   ├── config.py                    # Configuration management with validation
│   ├── exceptions.py                # Custom exception hierarchy for error handling
│   └── logger.py                    # Centralized logging with environment control
├── gui/                             # User interface layer
│   ├── main_window.py               # Main application window and graph display
│   ├── workers.py                   # Background thread workers for G-quality analysis
│   ├── settings_dialog.py           # Configuration interface
│   └── column_selector_dialog.py    # CSV column mapping interface
└── docs/
    └── testing-guide.md             # Comprehensive testing strategy (TDD approach)
```

### Core Architecture Principles

**Separation of Concerns**: Clean separation between core processing logic (`core/`) and GUI components (`gui/`). Core modules are GUI-agnostic and can be used independently.

**Asynchronous Processing**: Heavy computations run in `QThread` workers to maintain UI responsiveness. The `GQualityWorker` class handles time-intensive G-quality analysis with progress reporting.

**Intelligent Caching**: Processed data is cached in `results_AAT/cache/` using pickle and HDF5 formats. Cache invalidation occurs when source files, settings, or app version changes.

**Configuration Management**: JSON-based config with version tracking (`app_version` field) ensures backward compatibility. Default values are defined in `core/config.py:36-60`.

**Error Handling**: Custom exception hierarchy (`core/exceptions.py`) with:
- Base `AATException` class for all application errors
- Specific exceptions: `DataProcessingError`, `ColumnNotFoundError`, `SyncPointNotFoundError`
- Japanese error messages for improved user experience

### Data Processing Pipeline

1. **CSV Loading**: Auto-detect time and acceleration columns using keyword matching in `data_processor.py:19`
2. **Synchronization**: Detect sync points in acceleration data for precise time alignment
3. **Gravity Calculation**: Convert acceleration to gravity units using configurable constants
4. **Filtering**: Extract microgravity-relevant data segments based on threshold parameters
5. **Statistical Analysis**: Calculate minimum standard deviation windows across different time scales
6. **G-quality Analysis**: Multi-window analysis for microgravity quality assessment
7. **Export**: Generate Excel files and PNG graphs in structured `results_AAT/` directories

### Key Configuration Parameters

Critical settings in `config.json`:
- `sampling_rate`: Data frequency (default: 1000 Hz) - affects all time-based calculations
- `gravity_constant`: Reference gravity value (default: 9.797578 m/s²)
- `acceleration_threshold`: Sync point detection threshold (default: 0.5 m/s²)
- `window_size`: Primary analysis window (default: 0.1 seconds)
- `g_quality_start/end/step`: Multi-scale G-quality analysis parameters (0.1-0.5s, 0.05s step)
- `auto_calculate_g_quality`: Enable automatic G-quality analysis on file load
- `use_cache`: Enable/disable intelligent caching system
- `invert_inner_acceleration`: Invert Inner Capsule acceleration data (default: true)

### Threading and Performance

**Background Processing**: G-quality analysis runs in `GQualityWorker` threads to prevent UI blocking. Progress is reported via PyQt signals.

**Cache Strategy**: Two-tier caching:
- Processed DataFrames cached as pickle files
- Raw acceleration data cached as HDF5 for faster I/O
- Cache keys include file timestamp + settings hash + app version

**Memory Management**: Large datasets are processed in chunks during export operations to manage memory usage.

### Platform-Specific Considerations

**macOS Compatibility**: Special handling for PyQt6 warnings and TSM errors in `main.py:16-24`. Debug mode can be enabled with `AAT_DEBUG=1` environment variable.

**CI/CD Environment**: GitHub Actions workflow includes:
- X11 libraries for headless GUI testing (xvfb-run)
- System dependencies: libgl1-mesa-glx, libxkbcommon-x11-0, libxcb-* libraries
- Ruff version pinned to 0.8.4

**Error Handling**: Comprehensive logging with module-specific loggers. User-friendly error messages separate from detailed debug logs.

### Testing Strategy

**Test Framework**: pytest with pytest-qt for GUI testing (see `docs/testing-guide.md`)
- Unit tests for core modules (data processing, statistics)
- Integration tests for GUI components with pytest-qt
- Coverage targets: 80% overall, 90% for core modules

**Current Status**: Test infrastructure configured but tests not yet implemented. Use `pytest` when tests are added.

### Development Notes

**Configuration Changes**: When modifying data processing logic, increment `APP_VERSION` in `core/config.py:21` to invalidate existing caches.

**Adding New Statistics**: Statistical calculations are centralized in `core/statistics.py`. The `calculate_statistics()` function handles sliding window analysis.

**GUI Extensions**: Follow the worker thread pattern for any time-intensive operations. See `GQualityWorker` as reference implementation.

**Custom Exceptions**: Use the exception hierarchy in `core/exceptions.py` for consistent error handling. Create specific exception classes for new error conditions.

**Testing Data**: The application processes real scientific data - validate changes against known reference datasets.

### Output Structure

Results are saved in `results_AAT/` directory alongside source CSV files:
```
results_AAT/
├── <filename>.xlsx                  # Multi-sheet Excel with data and statistics
├── cache/                           # Processed data cache
│   ├── *.pickle                    # DataFrame cache files
│   └── *_raw.h5                    # Raw acceleration data cache
└── graphs/
    ├── <filename>_gl.png           # Gravity level graphs
    └── <filename>_gq.png           # G-quality analysis graphs
```

### Common Development Tasks

**Adding New Dependencies**:
```bash
# Add production dependency
uv pip install <package>
# Update pyproject.toml manually

# Add development dependency
uv pip install --dev <package>
# Update pyproject.toml [project.optional-dependencies.dev]
```

**Running Development Workflow**:
```bash
# Quick test cycle with uv
uv run python main.py               # Test changes
uv run ruff check . --fix           # Fix linting issues
uv run ruff format .                # Format code
uv run pytest                       # Run tests (when available)
```

**Adding New Export Formats**: Extend `core/export.py` and update output directory structure in `create_output_directories()`.

**Modifying Analysis Parameters**: Update defaults in `core/config.py` and ensure UI controls in `settings_dialog.py` are synchronized.

**Performance Optimization**: Profile using the existing logging infrastructure. Enable debug mode with `AAT_DEBUG=1 uv run python main.py`.

**Implementing New Column Types**: Update keyword matching in `data_processor.py:detect_columns()` and add corresponding UI in `column_selector_dialog.py`.

**Debugging Issues**: Set `AAT_DEBUG=1` environment variable for comprehensive logging. Check `core/logger.py` for logging configuration.

### Development Environment Setup

**Quick Start with uv**:
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
pip install uv                                    # Alternative method

# Setup project
uv venv                              # Create virtual environment
source .venv/bin/activate            # Activate environment
uv pip install -e ".[dev]"           # Install all dependencies

# Setup pre-commit hooks
uv run pre-commit install            # Install hooks
uv run pre-commit run --all-files    # Test hooks
```

**VSCode Integration**: Project includes `.vscode/settings.json` and `.vscode/extensions.json` for:
- Ruff auto-formatting on save
- Import organization  
- Recommended extensions: charliermarsh.ruff, ms-python.python, ms-python.debugpy
- uv support through Python extension

**GitHub Actions CI/CD**: Automated checks on push/PR to main and develop branches:
- Ruff linting and formatting validation (uses uv for fast installation)
- Basic import validation
- Runs in Ubuntu with GUI dependencies for PyQt6

### Troubleshooting Reference

See README.md for detailed troubleshooting guide including:
- CSV file format requirements and encoding issues
- Column detection problems and manual selection
- Cache-related issues and clearing procedures
- Platform-specific PyQt6 installation problems