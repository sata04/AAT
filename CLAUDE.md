# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AAT (Acceleration Analysis Tool) v9.1.0 is a Python desktop application for analyzing experimental data in microgravity environments. It processes acceleration data from Inner Capsule and Drag Shield sensors, calculates gravity levels, and performs statistical analysis to evaluate microgravity quality using a PyQt6 GUI.

## Essential Commands

### Development and Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Run with debug output (shows all logs)
AAT_DEBUG=1 python main.py

# Run with verbose output (shows INFO level logs)
python main.py --verbose
# or
python main.py -v

# Set custom log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
AAT_LOG_LEVEL=INFO python main.py

# Code quality and formatting
ruff check .                  # Lint all files
ruff check . --fix            # Lint and auto-fix issues
ruff format .                 # Format all files
ruff check . --diff           # Show what would be changed
```

### Dependencies
The project requires: PyQt6, matplotlib, numpy, pandas, openpyxl, tables, ruff

## Development Environment Setup

### Pre-commit Hooks (Recommended)
To ensure code quality consistency across all team members:

```bash
# Install pre-commit
pip install pre-commit

# Install the pre-commit hooks
pre-commit install

# Run pre-commit hooks on all files (optional)
pre-commit run --all-files
```

### VSCode Configuration
The project includes `.vscode/settings.json` and `.vscode/extensions.json` for consistent development experience:

**Recommended Extensions:**
- `charliermarsh.ruff` - Ruff linter and formatter
- `ms-python.python` - Python language support
- `ms-python.debugpy` - Python debugger

**Extension Installation:**
VSCode will automatically suggest these extensions when you open the project. You can also install them manually:
```bash
# Install Ruff extension (if using VSCode)
code --install-extension charliermarsh.ruff
```

**Alternative without Extensions:**
The project works without VSCode extensions. All code quality checks run via:
- Pre-commit hooks (before commits)
- Manual commands (`ruff check .`, `ruff format .`)
- CI/CD pipeline (GitHub Actions)

### GitHub Actions CI/CD
The project includes automated code quality checks via GitHub Actions:
- **Triggers:** Push and pull requests to `main` and `develop` branches
- **Checks:** Ruff linting and formatting validation
- **Test:** Basic import validation

### Environment Setup Priority
1. **Pre-commit hooks** (highest priority - runs before commits)
2. **GitHub Actions** (CI/CD validation)
3. **VSCode settings** (editor integration)
4. **Manual commands** (on-demand checking)

## Architecture Overview

### Project Structure
```
AAT/
├── main.py                     # Application entry point
├── config.json                 # Runtime configuration 
├── requirements.txt           
├── core/                      # Core processing logic
│   ├── data_processor.py      # CSV loading, column detection, gravity calculation
│   ├── statistics.py          # Statistical analysis and sliding window calculations
│   ├── cache_manager.py       # Intelligent data caching system
│   ├── export.py             # Excel and graph export functionality
│   ├── config.py             # Configuration management with validation
│   └── logger.py             # Centralized logging system
└── gui/                      # User interface layer
    ├── main_window.py        # Main application window and graph display
    ├── workers.py            # Background thread workers for G-quality analysis
    ├── settings_dialog.py    # Configuration interface
    └── column_selector_dialog.py  # CSV column mapping interface
```

### Core Architecture Principles

**Separation of Concerns**: Clean separation between core processing logic (`core/`) and GUI components (`gui/`). Core modules are GUI-agnostic and can be used independently.

**Asynchronous Processing**: Heavy computations run in `QThread` workers to maintain UI responsiveness. The `GQualityWorker` class handles time-intensive G-quality analysis with progress reporting.

**Intelligent Caching**: Processed data is cached in `results_AAT/cache/` using pickle and HDF5 formats. Cache invalidation occurs when source files, settings, or app version changes.

**Configuration Management**: JSON-based config with version tracking (`app_version` field) ensures backward compatibility. Default values are defined in `core/config.py:36-60`.

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

### Threading and Performance

**Background Processing**: G-quality analysis runs in `GQualityWorker` threads to prevent UI blocking. Progress is reported via PyQt signals.

**Cache Strategy**: Two-tier caching:
- Processed DataFrames cached as pickle files
- Raw acceleration data cached as HDF5 for faster I/O
- Cache keys include file timestamp + settings hash + app version

**Memory Management**: Large datasets are processed in chunks during export operations to manage memory usage.

### Platform-Specific Considerations

**macOS Compatibility**: Special handling for PyQt6 warnings and TSM errors in `main.py:16-24`. Debug mode can be enabled with `AAT_DEBUG=1` environment variable.

**Error Handling**: Comprehensive logging with module-specific loggers. User-friendly error messages separate from detailed debug logs.

### Development Notes

**Configuration Changes**: When modifying data processing logic, increment `APP_VERSION` in `core/config.py:21` to invalidate existing caches.

**Adding New Statistics**: Statistical calculations are centralized in `core/statistics.py`. The `calculate_statistics()` function handles sliding window analysis.

**GUI Extensions**: Follow the worker thread pattern for any time-intensive operations. See `GQualityWorker` as reference implementation.

**Testing Data**: The application processes real scientific data - validate changes against known reference datasets.

### Output Structure

Results are saved in `results_AAT/` directory alongside source CSV files:
```
results_AAT/
├── <filename>.xlsx           # Multi-sheet Excel with data and statistics
├── cache/                    # Processed data cache
│   ├── *.pickle             # DataFrame cache files
│   └── *_raw.h5             # Raw acceleration data cache
└── graphs/
    ├── <filename>_gl.png    # Gravity level graphs
    └── <filename>_gq.png    # G-quality analysis graphs
```

### Common Development Tasks

**Adding New Export Formats**: Extend `core/export.py` and update output directory structure in `create_output_directories()`.

**Modifying Analysis Parameters**: Update defaults in `core/config.py` and ensure UI controls in `settings_dialog.py` are synchronized.

**Performance Optimization**: Profile using the existing logging infrastructure. Enable debug mode for detailed timing information.