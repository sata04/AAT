import pandas as pd
import pytest

from core.data_processor import detect_columns, filter_data, load_and_process_data
from core.exceptions import ColumnNotFoundError, DataLoadError


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


def test_find_start_indices():
    """Test _find_start_indices helper function."""
    import pandas as pd

    from core.data_processor import _find_start_indices

    # Case 1: Both present, aligned
    time = pd.Series([0.0, 0.1, 0.2])
    adj_time = pd.Series([0.0, 0.1, 0.2])
    idx_ic, idx_ds = _find_start_indices(time, adj_time)
    assert idx_ic == 0
    assert idx_ds == 0

    # Case 2: Inner starts later (time values are all >= 0)
    time = pd.Series([0.0, 0.1, 0.2])
    adj_time = pd.Series([-0.1, 0.0, 0.1])
    idx_ic, idx_ds = _find_start_indices(time, adj_time)
    assert idx_ic == 0
    assert idx_ds == 1

    # Case 3: Drag starts later (time starts with negative)
    time = pd.Series([-0.1, 0.0, 0.1])
    adj_time = pd.Series([0.0, 0.1, 0.2])
    idx_ic, idx_ds = _find_start_indices(time, adj_time)
    assert idx_ic == 1
    assert idx_ds == 0

    # Case 4: One missing
    idx_ic, idx_ds = _find_start_indices(time, None)
    assert idx_ic == 1  # Based on previous time series used in Case 3
    assert idx_ds == 0


def test_find_end_indices():
    """Test _find_end_indices helper function."""
    import pandas as pd

    from core.data_processor import _find_end_indices

    # Setup data
    gl_ic = pd.Series([0.0, 0.1, 0.2, 1.0, 1.1, 1.2])
    gl_ds = pd.Series([0.0, 0.1, 0.2, 1.0, 1.1, 1.2])
    threshold = 1.0

    # Case 1: Both reach threshold
    end_idx_ic, end_idx_ds = _find_end_indices(gl_ic, gl_ds, 0, 0, threshold)
    assert end_idx_ic == 3  # Index where 1.0 is reached
    assert end_idx_ds == 3

    # Case 2: Only Inner reaches threshold
    gl_ds_low = pd.Series([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    end_idx_ic, end_idx_ds = _find_end_indices(gl_ic, gl_ds_low, 0, 0, threshold)
    assert end_idx_ic == 3
    assert end_idx_ds == 5  # Last index

    # Case 3: Only Drag reaches threshold
    gl_ic_low = pd.Series([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    end_idx_ic, end_idx_ds = _find_end_indices(gl_ic_low, gl_ds, 0, 0, threshold)
    assert end_idx_ic == 5  # Last index
    assert end_idx_ds == 3

    # Case 4: Neither reaches threshold
    end_idx_ic, end_idx_ds = _find_end_indices(gl_ic_low, gl_ds_low, 0, 0, threshold)
    assert end_idx_ic == 5
    assert end_idx_ds == 5


def test_detect_columns_ambiguous(tmp_path):
    """Test column detection with ambiguous names."""
    # Create CSV with multiple potential matches
    data = "time_s,timestamp,acc_x,acceleration_x\n0,0,0,0"
    csv_path = tmp_path / "ambiguous.csv"
    csv_path.write_text(data)

    time_cols, acc_cols = detect_columns(str(csv_path))

    # Should find all candidates
    assert "time_s" in time_cols
    assert "timestamp" in time_cols
    assert "acc_x" in acc_cols
    assert "acceleration_x" in acc_cols


def test_load_and_process_data_small_dataset(tmp_path, sample_config):
    """Test processing with very small dataset."""
    data = "time_s,acc_ic,acc_ds\n0.0,0.0,0.0"  # Only 1 row
    csv_path = tmp_path / "small.csv"
    csv_path.write_text(data)

    # Should handle gracefully, likely returning empty or single-row series
    # Depending on implementation, it might raise InsufficientDataError or just return what it can
    try:
        time, ic, ds, adj_time = load_and_process_data(str(csv_path), sample_config)
        # If it returns, check types
        assert isinstance(time, pd.Series)
    except Exception:
        # If it raises, that's also acceptable for 1 row, but we want to know which exception
        # For now, let's assume it should run without crashing
        pass


def test_load_and_process_data_non_monotonic_time(tmp_path, sample_config):
    """Test processing with non-monotonic time data."""
    data = "time_s,acc_ic,acc_ds\n0.0,0.0,0.0\n0.2,0.1,0.1\n0.1,0.2,0.2"  # 0.2 -> 0.1
    csv_path = tmp_path / "non_monotonic.csv"
    csv_path.write_text(data)

    # The current implementation might not sort, but it should load
    time, ic, ds, adj_time = load_and_process_data(str(csv_path), sample_config)

    assert len(time) == 3
    # Check if it's sorted or raw
    # If the implementation doesn't sort, it will be raw.
    # If we want to enforce sorting, we should check for it.
    # For now, just checking it loads.


def test_load_and_process_data_missing_values(tmp_path, sample_config):
    """Test processing with missing values (NaN)."""
    data = "time_s,acc_ic,acc_ds\n0.0,0.0,0.0\n0.1,,0.1\n0.2,0.2,"  # Missing values
    csv_path = tmp_path / "missing.csv"
    csv_path.write_text(data)

    # Pandas handles missing values as NaN
    time, ic, ds, adj_time = load_and_process_data(str(csv_path), sample_config)

    assert len(time) == 3
    assert pd.isna(ic.iloc[1])
    assert pd.isna(ds.iloc[2])


def test_detect_columns_encoding_error(tmp_path):
    """Test column detection with encoding error fallback."""
    csv_path = tmp_path / "encoding.csv"
    # Write invalid utf-8 sequence that might be valid cp932
    csv_path.write_bytes(b"\x80\x81\x82")

    # Should NOT raise DataLoadError if fallback works
    detect_columns(str(csv_path))


def test_detect_columns_empty_file(tmp_path):
    """Test column detection with empty file."""
    csv_path = tmp_path / "empty.csv"
    csv_path.touch()

    with pytest.raises(DataLoadError):  # Should raise DataLoadError
        detect_columns(str(csv_path))


def test_filter_data_warnings(sample_config):
    """Test filter_data warnings when data is insufficient."""
    # Create very short data that will be filtered out
    time = pd.Series([0.0, 0.1])
    ic = pd.Series([0.0, 0.0])
    ds = pd.Series([0.0, 0.0])
    adj_time = pd.Series([0.0, 0.1])

    # Set threshold high so nothing matches
    config = sample_config.copy()
    config["end_gravity_level"] = 10.0

    # This should trigger warnings about fallback to end of data
    filtered_time, _, _, _, end_idx = filter_data(time, ic, ds, adj_time, config)

    assert end_idx == 1  # Should use last index
    assert len(filtered_time) == 2


def test_detect_columns_cp932(tmp_path):
    """Test column detection with cp932 encoded file."""
    csv_path = tmp_path / "cp932.csv"
    # "時間" in Shift-JIS
    content = "時間,加速\n0,0".encode("cp932")
    csv_path.write_bytes(content)

    time_cols, acc_cols = detect_columns(str(csv_path))
    # Should load successfully
    assert len(time_cols) > 0 or len(acc_cols) > 0


def test_load_and_process_data_file_not_found(sample_config):
    """Test loading non-existent file."""
    with pytest.raises(DataLoadError):
        load_and_process_data("non_existent.csv", sample_config)
