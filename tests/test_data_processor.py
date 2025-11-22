import pytest

from core.data_processor import detect_columns, filter_data, load_and_process_data
from core.exceptions import ColumnNotFoundError


def test_detect_columns_returns_time_and_acceleration_candidates(sample_csv_file):
    time_columns, acceleration_columns = detect_columns(sample_csv_file)

    assert "time_s" in time_columns
    assert "acc_ic" in acceleration_columns
    assert "acc_ds" in acceleration_columns


def test_load_and_process_data_adjusts_time_and_gravity(sample_csv_file, sample_config):
    time_series, gravity_ic, gravity_ds, adjusted_time_drag = load_and_process_data(sample_csv_file, sample_config)

    assert time_series.iloc[0] == pytest.approx(0.0)
    assert adjusted_time_drag.iloc[0] == pytest.approx(0.0)
    assert gravity_ic.iloc[-1] == pytest.approx(2.0 / sample_config["gravity_constant"])
    assert gravity_ds.iloc[-1] == pytest.approx(1.5 / sample_config["gravity_constant"])


def test_load_and_process_data_raises_for_missing_columns(sample_csv_file, sample_config):
    broken_config = sample_config.copy()
    broken_config["time_column"] = "missing_column"

    with pytest.raises(ColumnNotFoundError):
        load_and_process_data(sample_csv_file, broken_config)


def test_filter_data_uses_end_gravity_level_threshold(sample_csv_file, sample_config):
    time_series, gravity_ic, gravity_ds, adjusted_time_drag = load_and_process_data(sample_csv_file, sample_config)

    filtered_time, filtered_ic, filtered_ds, filtered_adjusted_time, end_index = filter_data(
        time_series, gravity_ic, gravity_ds, adjusted_time_drag, sample_config
    )

    assert end_index == 4
    assert len(filtered_time) == 5
    assert filtered_time.iloc[-1] == pytest.approx(time_series.iloc[end_index])
    assert filtered_adjusted_time.iloc[0] == pytest.approx(0.0)
    assert filtered_ic.iloc[-1] == pytest.approx(2.0 / sample_config["gravity_constant"])
    assert filtered_ds.iloc[-1] == pytest.approx(1.5 / sample_config["gravity_constant"])


def test_load_and_process_data_inverts_inner_acceleration(sample_csv_file, sample_config):
    sample_config = sample_config | {"invert_inner_acceleration": True}
    _, gravity_ic, gravity_ds, _ = load_and_process_data(sample_csv_file, sample_config)

    assert gravity_ic.iloc[-1] == pytest.approx(-2.0 / sample_config["gravity_constant"])
    assert gravity_ds.iloc[-1] == pytest.approx(1.5 / sample_config["gravity_constant"])


def test_load_and_process_data_raises_when_sync_missing(tmp_path, sample_config):
    data = "\n".join(
        [
            "time_s,acc_ic,acc_ds",
            "0.0,5.0,5.0",
            "0.1,5.0,5.0",
        ]
    )
    csv_path = tmp_path / "nosync.csv"
    csv_path.write_text(data, encoding="utf-8")

    time_series, gravity_ic, gravity_ds, adjusted_time_drag = load_and_process_data(str(csv_path), sample_config)

    assert time_series.iloc[0] == pytest.approx(0.0)
    assert adjusted_time_drag.iloc[0] == pytest.approx(0.0)
    assert not gravity_ic.empty
    assert not gravity_ds.empty


def test_load_and_process_data_handles_single_inner_only(tmp_path, sample_config):
    data = "\n".join(
        [
            "time_s,acc_ic",
            "0.0,0.0",
            "0.1,0.5",
            "0.2,1.0",
        ]
    )
    csv_path = tmp_path / "single_inner.csv"
    csv_path.write_text(data, encoding="utf-8")

    sample_config = sample_config | {"use_drag_acceleration": False}

    time_series, gravity_ic, gravity_ds, adjusted_time_drag = load_and_process_data(str(csv_path), sample_config)

    assert not gravity_ic.empty
    assert gravity_ds.empty
    assert adjusted_time_drag.empty
    assert time_series.iloc[0] == pytest.approx(0.0)


def test_load_and_process_data_handles_single_drag_only(tmp_path, sample_config):
    data = "\n".join(
        [
            "time_s,acc_ds",
            "0.0,0.0",
            "0.1,0.5",
            "0.2,1.0",
        ]
    )
    csv_path = tmp_path / "single_drag.csv"
    csv_path.write_text(data, encoding="utf-8")

    sample_config = sample_config | {"use_inner_acceleration": False}

    time_series, gravity_ic, gravity_ds, adjusted_time_drag = load_and_process_data(str(csv_path), sample_config)

    assert gravity_ic.empty
    assert not gravity_ds.empty
    assert not adjusted_time_drag.empty
    assert adjusted_time_drag.iloc[0] == pytest.approx(0.0)
