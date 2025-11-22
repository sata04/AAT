from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from core.export import create_output_directories, export_data


def test_create_output_directories_respects_csv_dir(tmp_path):
    csv_dir = tmp_path / "csvs"
    csv_dir.mkdir()

    results_dir, graphs_dir = create_output_directories(str(csv_dir))

    assert results_dir == csv_dir / "results_AAT"
    assert graphs_dir == results_dir / "graphs"
    assert results_dir.exists()
    assert graphs_dir.exists()


def test_export_data_writes_excel_with_sheets(sample_config, raw_data_frame, tmp_path, dummy_message_box):
    csv_path = tmp_path / "data.csv"
    raw_data_frame.to_csv(csv_path, index=False)

    time_series = raw_data_frame["time_s"]
    adjusted_time = time_series - time_series.iloc[0]
    gl_ic = raw_data_frame["acc_ic"] / sample_config["gravity_constant"]
    gl_ds = raw_data_frame["acc_ds"] / sample_config["gravity_constant"]

    output_path = export_data(
        time=time_series,
        adjusted_time=adjusted_time,
        gravity_level_inner_capsule=gl_ic,
        gravity_level_drag_shield=gl_ds,
        file_path=str(csv_path),
        min_mean_inner_capsule=0.1,
        min_time_inner_capsule=0.0,
        min_std_inner_capsule=0.01,
        min_mean_drag_shield=0.2,
        min_time_drag_shield=0.0,
        min_std_drag_shield=0.02,
        graph_path=None,
        filtered_time=time_series,
        filtered_adjusted_time=adjusted_time,
        config=sample_config,
        raw_data=raw_data_frame,
    )

    assert Path(output_path).exists()
    workbook = load_workbook(output_path)
    assert "Gravity Level Data" in workbook.sheetnames
    assert "Gravity Level Statistics" in workbook.sheetnames
    assert "Acceleration Data" in workbook.sheetnames


def test_export_copies_graph_to_results_dir(sample_config, raw_data_frame, tmp_path, dummy_message_box):
    csv_path = tmp_path / "data.csv"
    raw_data_frame.to_csv(csv_path, index=False)

    graph_path = tmp_path / "graph.png"
    graph_path.write_bytes(b"pngdata")

    time_series = raw_data_frame["time_s"]
    adjusted_time = time_series - time_series.iloc[0]
    gl_ic = raw_data_frame["acc_ic"] / sample_config["gravity_constant"]
    gl_ds = raw_data_frame["acc_ds"] / sample_config["gravity_constant"]

    output_path = export_data(
        time=time_series,
        adjusted_time=adjusted_time,
        gravity_level_inner_capsule=gl_ic,
        gravity_level_drag_shield=gl_ds,
        file_path=str(csv_path),
        min_mean_inner_capsule=0.1,
        min_time_inner_capsule=0.0,
        min_std_inner_capsule=0.01,
        min_mean_drag_shield=0.2,
        min_time_drag_shield=0.0,
        min_std_drag_shield=0.02,
        graph_path=str(graph_path),
        filtered_time=time_series,
        filtered_adjusted_time=adjusted_time,
        config=sample_config,
        raw_data=raw_data_frame,
    )

    graphs_dir = Path(output_path).parent / "graphs"
    copied_graph = graphs_dir / f"{csv_path.stem}_gl.png"
    assert copied_graph.exists()


def test_export_skips_acceleration_sheet_when_columns_missing(sample_config, tmp_path, dummy_message_box):
    csv_path = tmp_path / "data.csv"
    data = pd.DataFrame({"time_s": [0.0, 0.1], "acc_x": [1.0, 1.1]})
    data.to_csv(csv_path, index=False)

    time_series = data["time_s"]
    adjusted_time = time_series - time_series.iloc[0]
    gl_ic = pd.Series([0.0, 0.1])
    gl_ds = pd.Series([0.0, 0.1])

    output_path = export_data(
        time=time_series,
        adjusted_time=adjusted_time,
        gravity_level_inner_capsule=gl_ic,
        gravity_level_drag_shield=gl_ds,
        file_path=str(csv_path),
        min_mean_inner_capsule=0.1,
        min_time_inner_capsule=0.0,
        min_std_inner_capsule=0.01,
        min_mean_drag_shield=0.2,
        min_time_drag_shield=0.0,
        min_std_drag_shield=0.02,
        graph_path=None,
        filtered_time=time_series,
        filtered_adjusted_time=adjusted_time,
        config=sample_config,
        raw_data=data,
    )

    workbook = load_workbook(output_path)
    assert "Gravity Level Data" in workbook.sheetnames
    assert "Acceleration Data" not in workbook.sheetnames
