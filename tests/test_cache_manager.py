import pickle
from pathlib import Path

import pandas as pd

from core.cache_manager import (
    delete_cache,
    generate_cache_id,
    get_cache_path,
    has_valid_cache,
    load_from_cache,
    save_to_cache,
)
from core.version import APP_VERSION


def test_generate_cache_id_changes_with_config(sample_config, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("time_s,acc_ic,acc_ds\n0,0,0\n")

    config = sample_config | {"app_version": APP_VERSION}
    cache_id_1 = generate_cache_id(str(csv_path), config)
    cache_id_2 = generate_cache_id(str(csv_path), config)

    tweaked_config = config | {"acceleration_threshold": 2.0}
    cache_id_3 = generate_cache_id(str(csv_path), tweaked_config)

    assert cache_id_1 == cache_id_2
    assert cache_id_1 != cache_id_3


def test_cache_roundtrip_with_raw_data(sample_config, raw_data_frame, tmp_path):
    csv_path = tmp_path / "data.csv"
    raw_data_frame.to_csv(csv_path, index=False)

    config = sample_config | {"app_version": APP_VERSION, "use_cache": True}
    cache_id = generate_cache_id(str(csv_path), config)

    processed_data = {"result": [1, 2, 3], "raw_data": raw_data_frame}

    assert save_to_cache(processed_data, str(csv_path), cache_id, config) is True

    cache_file = Path(get_cache_path(str(csv_path), cache_id))
    raw_cache_file = cache_file.with_name(cache_file.stem + "_raw.h5")
    assert cache_file.exists()

    has_cache, found_id = has_valid_cache(str(csv_path), config)
    assert has_cache is True
    assert found_id == cache_id

    loaded = load_from_cache(str(csv_path), cache_id)
    assert loaded is not None
    assert loaded["result"] == [1, 2, 3]
    pd.testing.assert_frame_equal(loaded["raw_data"], raw_data_frame)

    assert delete_cache(str(csv_path), cache_id) is True
    assert cache_file.exists() is False
    assert raw_cache_file.exists() is False


def test_has_valid_cache_respects_use_cache_flag(sample_config, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("time_s,acc_ic,acc_ds\n0,0,0\n")

    config = sample_config | {"use_cache": False}
    assert has_valid_cache(str(csv_path), config) == (False, None)


def test_has_valid_cache_detects_mtime_change(sample_config, raw_data_frame, tmp_path):
    csv_path = tmp_path / "data.csv"
    raw_data_frame.to_csv(csv_path, index=False)
    config = sample_config | {"app_version": APP_VERSION}

    cache_id = generate_cache_id(str(csv_path), config)
    save_to_cache({"raw_data": raw_data_frame}, str(csv_path), cache_id, config)

    # touch the source file to update mtime
    csv_path.write_text(csv_path.read_text() + "\n")

    is_valid, found_id = has_valid_cache(str(csv_path), config)
    assert is_valid is False
    assert found_id != cache_id


def test_load_from_cache_returns_none_on_version_mismatch(sample_config, raw_data_frame, tmp_path):
    csv_path = tmp_path / "data.csv"
    raw_data_frame.to_csv(csv_path, index=False)
    config = sample_config | {"app_version": APP_VERSION}

    cache_id = generate_cache_id(str(csv_path), config)
    save_to_cache({"raw_data": raw_data_frame}, str(csv_path), cache_id, config)

    cache_file = Path(get_cache_path(str(csv_path), cache_id))
    with cache_file.open("rb") as fh:
        data = pickle.load(fh)
    data["_metadata"]["app_version"] = "0.0.1"
    with cache_file.open("wb") as fh:
        pickle.dump(data, fh)

    assert load_from_cache(str(csv_path), cache_id) is None


def test_load_from_cache_handles_raw_data_read_error(monkeypatch, sample_config, raw_data_frame, tmp_path):
    csv_path = tmp_path / "data.csv"
    raw_data_frame.to_csv(csv_path, index=False)
    config = sample_config | {"app_version": APP_VERSION}

    cache_id = generate_cache_id(str(csv_path), config)
    save_to_cache({"raw_data": raw_data_frame}, str(csv_path), cache_id, config)

    monkeypatch.setattr("pandas.read_hdf", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("boom")))

    assert load_from_cache(str(csv_path), cache_id) is None
