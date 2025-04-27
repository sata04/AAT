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


def create_output_directories(csv_dir):
    """
    出力用ディレクトリ構造を作成する

    Args:
        csv_dir (str): 元のCSVファイルのディレクトリパス

    Returns:
        tuple: 作成した結果ディレクトリとグラフディレクトリのパス
    """
    # 結果ディレクトリとグラフディレクトリのパスを生成
    results_dir = os.path.join(csv_dir, "results_AAT")
    graphs_dir = os.path.join(results_dir, "graphs")

    # ディレクトリが存在しない場合は作成
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(graphs_dir, exist_ok=True)

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
    config=None,  # 設定パラメータを追加
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
        config (dict, optional): 設定パラメータ。指定されない場合はデフォルト値を使用

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

        # Excelファイルにデータと統計情報を書き込む
        with pd.ExcelWriter(output_file_path, engine="openpyxl") as writer:
            export_data.to_excel(writer, sheet_name="Gravity Level Data", index=False)
            stats_df.to_excel(writer, sheet_name="Gravity Level Statistics", index=False)

        # Gravity Level Graphシートは作成しない

        QMessageBox.information(
            None, "保存完了", f"Gravity Levelデータが {output_file_path} に保存されました\nグラフは {new_graph_path} に保存されました"
        )
        return output_file_path
    except PermissionError:
        raise ValueError(f"{output_file_path} に書き込みできません。権限を確認してください。")
    except Exception as e:
        raise ValueError(f"データの保存中にエラーが発生しました: {e}")


def export_g_quality_data(g_quality_data, original_file_path):
    """
    G-quality解析の結果をエクスポートする

    異なるウィンドウサイズでのG-quality評価結果をExcelファイルに追加または新規作成します。
    既存のExcelファイルがある場合は、G-quality Analysis シートを更新します。

    Args:
        g_quality_data (list): G-quality解析の結果データ
            各要素は (window_size, min_time_inner_capsule, min_mean_inner_capsule, min_std_inner_capsule,
                      min_time_drag_shield, min_mean_drag_shield, min_std_drag_shield) の形式のタプル
        original_file_path (str): 元のCSVファイルのパス

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
            workbook.remove(workbook.active)

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
