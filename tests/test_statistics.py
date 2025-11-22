import numpy as np
import pandas as pd
import pytest

from core.statistics import calculate_range_statistics, calculate_statistics


def test_calculate_statistics_finds_low_variance_window():
    time = pd.Series([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    gravity = pd.Series([0.5, 0.45, 0.1, 0.1, 0.1, 0.2])
    config = {"window_size": 0.2, "sampling_rate": 10}

    mean_abs, start_time, min_std = calculate_statistics(gravity, time, config)

    assert mean_abs == pytest.approx(0.1)
    assert start_time == pytest.approx(0.2)
    assert min_std == pytest.approx(0.0)


def test_calculate_statistics_returns_none_for_short_series():
    gravity = pd.Series([0.2])
    time = pd.Series([0.0])
    config = {"window_size": 0.2, "sampling_rate": 10}

    assert calculate_statistics(gravity, time, config) == (None, None, None)


def test_calculate_statistics_raises_when_lengths_mismatch():
    gravity = pd.Series([0.2, 0.3])
    time = pd.Series([0.0])
    config = {"window_size": 0.2, "sampling_rate": 10}

    with pytest.raises(ValueError):
        calculate_statistics(gravity, time, config)


def test_calculate_range_statistics_handles_empty_array():
    stats = calculate_range_statistics(np.array([]))

    assert stats["mean"] is None
    assert stats["abs_mean"] is None
    assert stats["std"] is None
    assert stats["min"] is None
    assert stats["max"] is None
    assert stats["range"] is None
    assert stats["count"] == 0


def test_calculate_range_statistics_computes_basic_stats():
    stats = calculate_range_statistics(np.array([1.0, -2.0, 3.0]))

    assert stats["mean"] == pytest.approx(0.6666, rel=1e-3)
    assert stats["abs_mean"] == pytest.approx(2.0)
    assert stats["std"] == pytest.approx(np.std([1.0, -2.0, 3.0]))
    assert stats["min"] == -2.0
    assert stats["max"] == 3.0
    assert stats["range"] == 5.0
    assert stats["count"] == 3
