#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データエクスポートモジュール

処理されたデータと解析結果をExcelファイルにエクスポートする機能を提供します。
重力レベルデータとグラフ、G-quality解析結果を保存します。
"""

import os

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from PyQt6.QtWidgets import QMessageBox

from core.logger import get_logger, log_exception

# モジュール用のロガーを初期化
logger = get_logger("export")


def create_output_directories(csv_dir=None):
    """
    出力用ディレクトリ構造を作成する

    CSVファイルがあるディレクトリに `results_AAT/graphs` ディレクトリを作成します。
    csv_dir が指定されていない場合は、プロジェクトルートにフォールバックします。

    Args:
        csv_dir (str, optional): CSVファイルのディレクトリパス。指定されていればそのディレクトリに作成

    Returns:
        tuple: 作成した結果ディレクトリとグラフディレクトリのパス
    """
    # プロジェクトルートを取得（フォールバック用）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    # 基準ディレクトリ: csv_dir が指定されていればCSVファイルのディレクトリを使用し、未指定時はプロジェクトルートをフォールバック
    base_dir = csv_dir if csv_dir else project_root

    # デバッグ情報を追加
    logger.debug(f"create_output_directories called with csv_dir: {csv_dir}")

    # csv_dirが空文字列や無効な場合の警告
    if csv_dir is None:
        logger.warning("csv_dir is None, falling back to project root")
    elif csv_dir == "":
        logger.warning("csv_dir is empty string, falling back to project root")

    logger.debug(f"Using base_dir: {base_dir}")

    results_dir = os.path.join(base_dir, "results_AAT")
    graphs_dir = os.path.join(results_dir, "graphs")

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(graphs_dir, exist_ok=True)

    logger.debug(f"Created directories: results={results_dir}, graphs={graphs_dir}")

    return results_dir, graphs_dir


def export_data(
    time,
    adjusted_time,
    gravity_level_inner_capsule,
    gravity_level_drag_shield,
    file_path,
    min_mean_inner_capsule,
    min_time_inner_capsule,
    min_std_inner_capsule,
    min_mean_drag_shield,
    min_time_drag_shield,
    min_std_drag_shield,
    graph_path,
    filtered_time,  # フィルタリング済みの時間データを追加
    filtered_adjusted_time,  # フィルタリング済みの調整時間データを追加
    config=None,  # 設定パラメータを追加
    raw_data=None,  # 元のCSVデータを追加
):
    """
    処理されたデータとグラフをExcelにエクスポートする

    重力レベルデータと統計情報を含むExcelファイルを作成します。
    グラフは別途グラフディレクトリに保存します。
    既存のファイルが存在する場合は、上書きするかどうかを確認します。

    Args:
        time (pandas.Series): 時間データ
        adjusted_time (pandas.Series): 調整された時間データ
        gravity_level_inner_capsule (pandas.Series): Inner Capsuleの重力レベル
        gravity_level_drag_shield (pandas.Series): Drag Shieldの重力レベル
        file_path (str): 元のCSVファイルのパス
        min_mean_inner_capsule (float): Inner Capsuleの最小標準偏差ウィンドウの平均値
        min_time_inner_capsule (float): Inner Capsuleの最小標準偏差ウィンドウの開始時間
        min_std_inner_capsule (float): Inner Capsuleの最小標準偏差値
        min_mean_drag_shield (float): Drag Shieldの最小標準偏差ウィンドウの平均値
        min_time_drag_shield (float): Drag Shieldの最小標準偏差ウィンドウの開始時間
        min_std_drag_shield (float): Drag Shieldの最小標準偏差値
        graph_path (str): 保存されたグラフの画像ファイルパス
        filtered_time (pandas.Series): フィルタリングされた時間データ
        filtered_adjusted_time (pandas.Series): フィルタリングされた調整時間データ
        config (dict, optional): 設定パラメータ。指定されない場合はデフォルト値を使用
        raw_data (pandas.DataFrame, optional): 元のCSVデータ。加速度データ出力用

    Returns:
        str: 出力されたExcelファイルのパス

    Raises:
        ValueError: データのエクスポート中にエラーが発生した場合
    """
    # CSVファイルのディレクトリとファイル名を取得
    csv_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    # 出力ディレクトリ構造を作成
    results_dir, graphs_dir = create_output_directories(csv_dir)

    # 出力ファイルパスの設定（シンプルな名前を使用）
    output_file_path = os.path.join(results_dir, f"{base_name}.xlsx")

    # グラフファイルの新しいパスを設定（短い名前を使用）
    new_graph_path = os.path.join(graphs_dir, f"{base_name}_gl.png")

    # 既存グラフが元のパスに存在する場合、新しいパスにコピー
    if os.path.exists(graph_path) and graph_path != new_graph_path:
        import shutil

        shutil.copy2(graph_path, new_graph_path)

    # 既存ファイルの確認
    if os.path.exists(output_file_path):
        reply = QMessageBox.question(
            None,
            "確認",
            f"出力ファイルが既に存在します:\n{output_file_path}\n上書きしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            # 新しいファイル名を生成（連番を付加）
            counter = 1
            while os.path.exists(os.path.join(results_dir, f"{base_name}_{counter}.xlsx")):
                counter += 1
            output_file_path = os.path.join(results_dir, f"{base_name}_{counter}.xlsx")

    try:
        # 共通の時間軸を作成
        start_time = max(time.min(), adjusted_time.min())
        end_time = min(time.max(), adjusted_time.max())

        # configが指定されていない場合のデフォルト値
        if config is None:
            config = {}

        # 時間間隔を計算（サンプリングレートに基づく）
        sampling_rate = config.get("sampling_rate", 1000)  # 設定からサンプリングレートを取得、デフォルトは1000Hz
        time_step = 1.0 / sampling_rate

        # 共通の時間軸を生成
        unified_time = np.arange(start_time, end_time + time_step, time_step)

        # 各データを共通の時間軸に補間
        interpolated_inner_capsule = np.interp(unified_time, time, gravity_level_inner_capsule)
        interpolated_drag_shield = np.interp(unified_time, adjusted_time, gravity_level_drag_shield)

        # データフレームの作成（統一された時間軸）
        export_data = pd.DataFrame(
            {
                "Time (s)": unified_time,
                "Gravity Level (Inner Capsule) (G)": interpolated_inner_capsule,
                "Gravity Level (Drag Shield) (G)": interpolated_drag_shield,
            }
        )

        # 統計情報のデータフレームを作成
        stats_df = pd.DataFrame(
            {
                "Statistic": [
                    "Inner Capsule: Mean Gravity Level of the interval with the smallest standard deviation(G)",
                    "Inner Capsule: Time at smallest Standard Deviation(s)",
                    "Inner Capsule: smallest Standard Deviation(G)",
                    "Drag Shield: Mean Gravity Level of the interval with the smallest standard deviation(G)",
                    "Drag Shield: Time at smallest Standard Deviation(s)",
                    "Drag Shield: smallest Standard Deviation(G)",
                ],
                "Value": [
                    min_mean_inner_capsule,
                    min_time_inner_capsule,
                    min_std_inner_capsule,
                    min_mean_drag_shield,
                    min_time_drag_shield,
                    min_std_drag_shield,
                ],
            }
        )

        # トリミング範囲の加速度データを準備
        acceleration_data = None
        if raw_data is not None:
            # 元のCSVデータが提供されている場合
            try:
                # 設定から列名を取得
                time_column = config.get("time_column")
                acceleration_inner_column = config.get("acceleration_column_inner_capsule")
                acceleration_drag_column = config.get("acceleration_column_drag_shield")

                logger.info(
                    f"加速度データの処理開始: 時間列={time_column}, 内カプセル加速度列={acceleration_inner_column}, 外カプセル加速度列={acceleration_drag_column}"
                )
                logger.debug(f"元データの列: {raw_data.columns.tolist()}")

                # 必要な列が存在するか確認
                if all(col is not None for col in [time_column, acceleration_inner_column, acceleration_drag_column]):
                    column_exist = True
                    missing_cols = []

                    # 列名が実際に存在するか確認
                    for col, col_name in [
                        (time_column, "時間列"),
                        (acceleration_inner_column, "内カプセル加速度列"),
                        (acceleration_drag_column, "外カプセル加速度列"),
                    ]:
                        if col not in raw_data.columns:
                            column_exist = False
                            missing_cols.append(f"{col_name}({col})")

                    if column_exist:
                        try:
                            # 元のInner CapsuleとDrag Shieldのデータを準備
                            # 注: 全時間軸上のデータを使用（フィルタリング済みではなく、全データを使用）
                            orig_time_data = raw_data[time_column].values.astype(float)
                            orig_inner_accel = raw_data[acceleration_inner_column].values.astype(float)
                            orig_drag_accel = raw_data[acceleration_drag_column].values.astype(float)

                            # drag shield用の元時間を同期点で調整
                            acc_thresh = config.get("acceleration_threshold", 1.0)
                            sync_mask = np.abs(orig_drag_accel) < acc_thresh
                            if sync_mask.any():
                                sync_idx = np.where(sync_mask)[0][0]
                                orig_adjusted_time = orig_time_data - orig_time_data[sync_idx]
                            else:
                                orig_adjusted_time = orig_time_data - orig_time_data[0]

                            # 共通の時間軸に合わせて加速度データを補間
                            inner_accel_interp = np.interp(unified_time, orig_time_data, orig_inner_accel)
                            drag_accel_interp = np.interp(unified_time, orig_adjusted_time, orig_drag_accel)
                            acceleration_data = pd.DataFrame(
                                {
                                    "Time (s)": unified_time,
                                    "Acceleration (Inner Capsule) (m/s²)": inner_accel_interp,
                                    "Acceleration (Drag Shield) (m/s²)": drag_accel_interp,
                                }
                            )
                            logger.info(f"共通時間軸で加速度データを作成: {len(acceleration_data)}行")

                        except Exception as e:
                            logger.error(f"加速度データの作成中にエラー: {e}")
                            acceleration_data = None
                    else:
                        logger.warning(f"必要な列が見つかりません: {missing_cols}")
                        # 列選択ダイアログで選択された列がraw_dataに存在しない場合の対応
                        QMessageBox.warning(
                            None,
                            "列が見つかりません",
                            f"必要な列が見つかりません: \n{', '.join(missing_cols)}\n\n"
                            + "加速度データがシートに追加されません。\n"
                            + "CSVファイルを選択する際、正しい列を選んでください。",
                        )
                else:
                    logger.warning(
                        "設定に必要な列名が定義されていません。"
                        + f"時間列={time_column}, "
                        + f"内カプセル加速度列={acceleration_inner_column}, "
                        + f"外カプセル加速度列={acceleration_drag_column}"
                    )
                    # 設定に列名が定義されていない場合の対応
                    QMessageBox.warning(
                        None, "設定エラー", "加速度データの列情報が設定されていません。\n" + "CSVファイルを再度選択して、必要な列を指定してください。"
                    )
            except Exception as e:
                log_exception(e, "加速度データの準備中にエラーが発生しました")
                acceleration_data = None

        # Excelファイルにデータと統計情報を書き込む
        with pd.ExcelWriter(output_file_path, engine="openpyxl") as writer:
            export_data.to_excel(writer, sheet_name="Gravity Level Data", index=False)
            stats_df.to_excel(writer, sheet_name="Gravity Level Statistics", index=False)
            if acceleration_data is not None:
                acceleration_data.to_excel(writer, sheet_name="Acceleration Data", index=False)
                logger.info(f"加速度データをシートに追加しました: {len(acceleration_data)}行")
            else:
                logger.warning("加速度データが作成されなかったため、シートに追加されません")

        # 保存完了メッセージ - フォルダ名だけを表示するように変更
        graphs_folder = os.path.basename(os.path.dirname(new_graph_path))
        message = f"Gravity Levelデータが {output_file_path} に保存されました\nグラフは {graphs_folder} フォルダに保存されました"
        QMessageBox.information(None, "保存完了", message)

        return output_file_path
    except PermissionError:
        error_msg = f"{output_file_path} に書き込みできません。権限を確認してください。"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"データの保存中にエラーが発生しました: {e}"
        log_exception(e, error_msg)
        raise ValueError(error_msg)


def export_g_quality_data(g_quality_data, original_file_path, g_quality_graph_path=None):
    """
    G-quality解析の結果をエクスポートする

    異なるウィンドウサイズでのG-quality評価結果をExcelファイルに追加または新規作成します。
    既存のExcelファイルがある場合は、G-quality Analysis シートを更新します。
    また、G-qualityグラフが提供されている場合は、指定されたディレクトリにコピーします。

    Args:
        g_quality_data (list): G-quality解析の結果データ
            各要素は (window_size, min_time_inner_capsule, min_mean_inner_capsule, min_std_inner_capsule,
                      min_time_drag_shield, min_mean_drag_shield, min_std_drag_shield) の形式のタプル
        original_file_path (str): 元のCSVファイルのパス
        g_quality_graph_path (str, optional): G-qualityグラフの画像ファイルパス。指定された場合はグラフをコピーします。

    Returns:
        str or None: 出力されたExcelファイルのパス、または失敗した場合はNone

    Raises:
        ValueError: データのエクスポート中にエラーが発生した場合
    """
    # CSVファイルのディレクトリとファイル名を取得
    csv_dir = os.path.dirname(original_file_path)
    base_name = os.path.splitext(os.path.basename(original_file_path))[0]

    # 出力ディレクトリ構造を作成
    results_dir, graphs_dir = create_output_directories(csv_dir)

    # G-qualityグラフの処理
    if g_quality_graph_path and os.path.exists(g_quality_graph_path):
        # グラフファイルの新しいパスを設定（短い名前を使用）
        new_graph_path = os.path.join(graphs_dir, f"{base_name}_gq.png")

        # 常に上書きコピーを実行（パス比較を行わない）
        import shutil

        try:
            shutil.copy2(g_quality_graph_path, new_graph_path)
            logger.info(f"G-qualityグラフを保存しました: {g_quality_graph_path} -> {new_graph_path}")
        except Exception as e:
            logger.warning(f"G-qualityグラフの保存中にエラーが発生しました: {e}")

    # データフレームの作成
    df = pd.DataFrame(
        g_quality_data,
        columns=[
            "Window Size (s)",
            "Inner Capsule: Time at smallest Standard Deviation(s)",
            "Inner Capsule: Mean Gravity Level of the interval with the smallest standard deviation(G)",
            "Inner Capsule: smallest Standard Deviation(G)",
            "Drag Shield: Time at smallest Standard Deviation(s)",
            "Drag Shield: Mean Gravity Level of the interval with the smallest standard deviation(G)",
            "Drag Shield: smallest Standard Deviation(G)",
        ],
    )

    # 出力ファイルパスの設定
    output_file_path = os.path.join(results_dir, f"{base_name}.xlsx")

    try:
        # 既存のExcelファイルを読み込むか、新規作成
        try:
            workbook = load_workbook(output_file_path)
        except FileNotFoundError:
            workbook = Workbook()
            # デフォルトのシートを削除（後で必要なシートを追加する）
            sheet_to_remove = workbook.active
            if sheet_to_remove is not None:
                workbook.remove(sheet_to_remove)

        # G-quality Analysis シートを作成または更新
        sheet_name = "G-quality Analysis"
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            # 既存のシートをクリア
            for row in sheet[sheet.min_row : sheet.max_row]:
                for cell in row:
                    cell.value = None
        else:
            sheet = workbook.create_sheet(title=sheet_name)

        # データをシートに書き込む（1行目から開始）
        for row in dataframe_to_rows(df, index=False, header=True):
            sheet.append(row)

        # ファイルを保存
        workbook.save(output_file_path)
        return output_file_path
    except PermissionError:
        raise ValueError(f"{output_file_path} に書き込みできません。ファイルが開かれている可能性があります。")
    except Exception as e:
        raise ValueError(f"データの保存中にエラーが発生しました: {e}")
