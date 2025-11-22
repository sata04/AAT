import time
from unittest.mock import patch

import pandas as pd
from PySide6.QtCore import QThread

from gui.workers import GQualityWorker


def test_worker_initialization(sample_config):
    """Test worker initialization."""
    time_data = pd.Series([0.0, 0.1, 0.2])
    gravity_inner = pd.Series([0.0, 0.01, 0.02])
    gravity_drag = pd.Series([0.0, 0.01, 0.02])

    worker = GQualityWorker(time_data, gravity_inner, gravity_drag, sample_config, filtered_adjusted_time=time_data)

    assert worker.filtered_time is time_data
    assert worker.filtered_gravity_level_inner_capsule is gravity_inner
    assert worker.filtered_gravity_level_drag_shield is gravity_drag
    assert worker.config == sample_config
    assert worker.is_running


def test_g_quality_runs_with_single_sensor(sample_config):
    """Test worker runs with only inner capsule data."""
    config = sample_config | {"g_quality_start": 0.1, "g_quality_end": 0.2, "g_quality_step": 0.1}

    time_data = pd.Series([0.0, 0.1, 0.2, 0.3])
    gravity_inner = pd.Series([0.0, 0.01, 0.02, 0.03])
    gravity_drag = pd.Series(dtype=float)  # Dragなし

    worker = GQualityWorker(
        time_data, gravity_inner, gravity_drag, config, filtered_adjusted_time=pd.Series(dtype=float)
    )
    worker.run()

    results = worker.get_results()
    assert results, "InnerのみでもG-quality結果が得られるはずです"
    assert len(results) > 0
    # Result format: (window, time_ic, mean_ic, std_ic, time_ds, mean_ds, std_ds)
    assert results[0][2] is not None  # Inner mean
    assert results[0][5] is None  # Drag mean should be None when absent


def test_worker_signals(qtbot, sample_config):
    """Test that worker emits correct signals during execution."""
    time_data = pd.Series([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    gravity_inner = pd.Series([0.0] * 6)
    gravity_drag = pd.Series([0.0] * 6)

    config = sample_config | {"g_quality_start": 0.1, "g_quality_end": 0.3, "g_quality_step": 0.1}

    worker = GQualityWorker(time_data, gravity_inner, gravity_drag, config, filtered_adjusted_time=time_data)

    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.run()

    assert blocker.signal_triggered


def test_worker_stop(qtbot, sample_config):
    """Test that worker can be stopped mid-execution."""
    # Create large dataset to ensure it runs long enough to be stopped
    time_data = pd.Series(range(1000)) * 0.01
    gravity_inner = pd.Series([0.0] * 1000)
    gravity_drag = pd.Series([0.0] * 1000)

    config = sample_config | {"g_quality_start": 0.1, "g_quality_end": 5.0, "g_quality_step": 0.1}

    worker = GQualityWorker(time_data, gravity_inner, gravity_drag, config, filtered_adjusted_time=time_data)

    # Mock calculate_statistics to slow down execution
    with patch("gui.workers.calculate_statistics") as mock_calc:

        def slow_calc(*args, **kwargs):
            time.sleep(0.01)
            return (0.0, 0.0, 0.0)

        mock_calc.side_effect = slow_calc

        # Start worker in a separate thread to simulate real usage
        thread = QThread()
        worker.moveToThread(thread)

        worker.finished.connect(thread.quit)
        thread.started.connect(worker.run)

        thread.start()

        # Let it run for a bit
        qtbot.wait(100)

        # Stop the worker
        worker.stop()

        # Wait for thread to finish
        qtbot.waitUntil(lambda: thread.isFinished() or not worker.is_running, timeout=2000)

        if thread.isRunning():
            thread.quit()
            thread.wait()

        assert not worker.is_running


def test_worker_error_handling(qtbot, sample_config):
    """Test that worker handles exceptions gracefully."""
    time_data = pd.Series([0.0, 0.1])
    gravity_inner = pd.Series([0.0, 0.1])
    gravity_drag = pd.Series([0.0, 0.1])

    worker = GQualityWorker(time_data, gravity_inner, gravity_drag, sample_config, filtered_adjusted_time=time_data)

    # Mock calculate_statistics to raise exception
    with patch("gui.workers.calculate_statistics", side_effect=ValueError("Test Error")):
        with qtbot.waitSignal(worker.finished) as blocker:
            worker.run()

        # Should return empty list on error
        assert blocker.args[0] == []


def test_worker_empty_data(sample_config):
    """Test worker behavior with empty data."""
    empty = pd.Series(dtype=float)

    worker = GQualityWorker(empty, empty, empty, sample_config, filtered_adjusted_time=empty)

    worker.run()
    results = worker.get_results()
    assert len(results) == 0
