import pandas as pd

from gui.workers import GQualityWorker


def test_g_quality_runs_with_single_sensor(sample_config):
    config = sample_config | {"g_quality_start": 0.1, "g_quality_end": 0.2, "g_quality_step": 0.1}

    time = pd.Series([0.0, 0.1, 0.2, 0.3])
    gravity_inner = pd.Series([0.0, 0.01, 0.02, 0.03])
    gravity_drag = pd.Series(dtype=float)  # Dragなし

    worker = GQualityWorker(time, gravity_inner, gravity_drag, config, filtered_adjusted_time=pd.Series(dtype=float))
    worker.run()

    results = worker.get_results()
    assert results, "InnerのみでもG-quality結果が得られるはずです"
    assert results[0][2] is not None  # Inner mean
    assert results[0][5] is None  # Drag mean should be None when absent
