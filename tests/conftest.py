import atexit
import importlib
import json
import os
import shutil
import tempfile
from pathlib import Path

# PySide6-Essentials + shiboken6 環境でのpytest-qt互換性修正
# pytest-qtはPySide6.__version__を参照するが、PySide6-Essentialsには含まれない
import PySide6

if not hasattr(PySide6, "__version__"):
    import shiboken6

    PySide6.__version__ = shiboken6.__version__
    PySide6.__version_info__ = shiboken6.__version_info__

import numpy as np
import pandas as pd
import pytest


def _ensure_temp_env_dir(env_var: str, prefix: str) -> Path:
    """
    Ensure the given env var points to a writable temp directory.

    Returns the resolved path so tests can rely on a predictable, isolated location.
    """
    existing = os.environ.get(env_var)
    if existing:
        path = Path(existing)
        path.mkdir(parents=True, exist_ok=True)
        return path

    temp_dir = Path(tempfile.mkdtemp(prefix=f"aat-{prefix}-"))
    atexit.register(shutil.rmtree, temp_dir, ignore_errors=True)
    os.environ[env_var] = str(temp_dir)
    return temp_dir


# Force Qt into headless mode before pytest-qt creates the QApplication.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Keep config/cache writes inside temp directories to avoid polluting the host.
_ensure_temp_env_dir("AAT_CONFIG_DIR", "config")
_ensure_temp_env_dir("MPLCONFIGDIR", "mpl")


@pytest.fixture
def sample_config() -> dict[str, float | int | bool | str]:
    return {
        "time_column": "time_s",
        "acceleration_column_inner_capsule": "acc_ic",
        "acceleration_column_drag_shield": "acc_ds",
        "gravity_constant": 9.8,
        "acceleration_threshold": 1.0,
        "end_gravity_level": 0.15,
        "min_seconds_after_start": 0.2,
        "sampling_rate": 10,
        "window_size": 0.2,
        "invert_inner_acceleration": False,
        "g_quality_start": 0.1,
        "g_quality_end": 0.3,
        "g_quality_step": 0.1,
        "use_inner_acceleration": True,
        "use_drag_acceleration": True,
    }


@pytest.fixture
def sample_csv_file(tmp_path) -> str:
    time = np.arange(0, 0.6, 0.1)
    acc_ic = np.array([0.0, 0.0, 0.98, 0.98, 2.0, 2.0], dtype=float)
    acc_ds = np.array([0.0, 0.0, 0.98, 0.98, 1.5, 1.5], dtype=float)

    df = pd.DataFrame(
        {
            "time_s": time,
            "acc_ic": acc_ic,
            "acc_ds": acc_ds,
        }
    )

    file_path = tmp_path / "sample.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)


@pytest.fixture
def raw_data_frame() -> pd.DataFrame:
    time = np.arange(0, 0.6, 0.1)
    acc_ic = np.array([0.0, 0.0, 0.98, 0.98, 2.0, 2.0], dtype=float)
    acc_ds = np.array([0.0, 0.0, 0.98, 0.98, 1.5, 1.5], dtype=float)

    return pd.DataFrame(
        {
            "time_s": time,
            "acc_ic": acc_ic,
            "acc_ds": acc_ds,
        }
    )


@pytest.fixture
def dummy_message_box(monkeypatch):
    class DummyMessageBox:
        StandardButton = type("StandardButton", (), {"Yes": 1, "No": 2})

        @staticmethod
        def question(*args, **kwargs):
            return DummyMessageBox.StandardButton.Yes

        @staticmethod
        def information(*args, **kwargs):
            return None

        @staticmethod
        def warning(*args, **kwargs):
            return None

    for module_path in ("core.export", "core.config"):
        module = importlib.import_module(module_path)
        if hasattr(module, "QMessageBox"):
            monkeypatch.setattr(f"{module_path}.QMessageBox", DummyMessageBox)
    return DummyMessageBox


@pytest.fixture
def app_root_with_default(tmp_path, monkeypatch):
    app_root = tmp_path / "app_root"
    config_dir = app_root / "config"
    config_dir.mkdir(parents=True)

    default_config = {
        "time_column": "time_col",
        "acceleration_column_inner_capsule": "acc_ic",
        "acceleration_column_drag_shield": "acc_ds",
        "sampling_rate": 10,
        "gravity_constant": 9.8,
        "use_cache": True,
    }
    (config_dir / "config.default.json").write_text(json.dumps(default_config), encoding="utf-8")

    monkeypatch.setattr("core.config._get_app_root", lambda: app_root)
    return default_config, app_root
