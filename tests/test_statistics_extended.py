"""Extended edge-case tests for core/statistics.py."""

import numpy as np
import pandas as pd
import pytest

from core.statistics import calculate_range_statistics, calculate_statistics

# --- calculate_statistics edge cases ---


def test_calculate_statistics_all_nan():
    """All-NaN data should return (None, None, None)."""
    gravity = pd.Series([np.nan] * 200)
    time = pd.Series(np.arange(200) / 1000.0)
    result = calculate_statistics(gravity, time, {"window_size": 0.1, "sampling_rate": 1000})
    assert result == (None, None, None)


def test_calculate_statistics_partial_nan():
    """Data with some NaN values should still compute a result."""
    data = np.zeros(200)
    data[50:60] = np.nan
    gravity = pd.Series(data)
    time = pd.Series(np.arange(200) / 1000.0)
    result = calculate_statistics(gravity, time, {"window_size": 0.1, "sampling_rate": 1000})
    assert result[0] is not None


def test_calculate_statistics_constant_data():
    """Constant data should yield zero std and constant mean."""
    gravity = pd.Series([0.5] * 200)
    time = pd.Series(np.arange(200) / 1000.0)
    mean, t, std = calculate_statistics(gravity, time, {"window_size": 0.1, "sampling_rate": 1000})
    assert std is not None
    assert std < 1e-10
    assert abs(mean - 0.5) < 1e-10


def test_calculate_statistics_single_window():
    """Data length exactly equals window size — one valid window."""
    gravity = pd.Series([1.0, 2.0, 3.0])
    time = pd.Series([0.0, 0.001, 0.002])
    mean, t, std = calculate_statistics(gravity, time, {"window_size": 0.003, "sampling_rate": 1000})
    assert mean is not None


def test_calculate_statistics_window_larger_than_data():
    """Window larger than data should return (None, None, None)."""
    gravity = pd.Series([1.0, 2.0])
    time = pd.Series([0.0, 0.001])
    result = calculate_statistics(gravity, time, {"window_size": 0.01, "sampling_rate": 1000})
    assert result == (None, None, None)


def test_calculate_statistics_default_config_values():
    """Missing config keys should use defaults (window_size=0.1, sampling_rate=1000)."""
    gravity = pd.Series(np.random.default_rng(42).standard_normal(200) * 0.01)
    time = pd.Series(np.arange(200) / 1000.0)
    result = calculate_statistics(gravity, time, {})
    assert result[0] is not None


def test_calculate_statistics_negative_values():
    """Negative gravity values — abs_mean should be positive."""
    gravity = pd.Series([-0.1, -0.2, -0.05, -0.15, -0.1] * 40)
    time = pd.Series(np.arange(200) / 1000.0)
    mean, t, std = calculate_statistics(gravity, time, {"window_size": 0.1, "sampling_rate": 1000})
    assert mean is not None
    assert mean > 0


# --- calculate_range_statistics edge cases ---


def test_calculate_range_statistics_with_nan():
    """NaN propagates to mean/std but count should reflect array length."""
    data = np.array([1.0, 2.0, np.nan, 4.0])
    result = calculate_range_statistics(data)
    assert result["count"] == 4


def test_calculate_range_statistics_single_value():
    """Single-element array: std=0, range=0."""
    data = np.array([5.0])
    result = calculate_range_statistics(data)
    assert result["mean"] == 5.0
    assert result["std"] == 0.0
    assert result["range"] == 0.0
    assert result["count"] == 1


def test_calculate_range_statistics_all_same():
    """Array of identical values: std=0, range=0."""
    data = np.array([3.0, 3.0, 3.0, 3.0])
    result = calculate_range_statistics(data)
    assert result["mean"] == pytest.approx(3.0)
    assert result["std"] == pytest.approx(0.0)
    assert result["range"] == pytest.approx(0.0)


def test_calculate_range_statistics_large_range():
    """Verify range = max - min with large spread."""
    data = np.array([-1000.0, 1000.0])
    result = calculate_range_statistics(data)
    assert result["range"] == pytest.approx(2000.0)
    assert result["min"] == pytest.approx(-1000.0)
    assert result["max"] == pytest.approx(1000.0)
