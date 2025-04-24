# core/export.py
# データのエクスポート機能

import os

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows
from PyQt6.QtWidgets import QMessageBox


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
):
    """
    処理されたデータとグラフをExcelにエクスポートする
    """
    # 出力ファイルパスの設定
    output_file_path = os.path.splitext(file_path)[0] + "_processed.xlsx"

    # 既存ファイルの確認
    if os.path.exists(output_file_path):
        # 元のファイル名から日付部分を抽出して処理済みかを判断
        base_name = os.path.basename(file_path)
        if "_processed" in base_name:
            # 既に処理済みのファイルの場合
            reply = QMessageBox.question(
                None,
                "確認",
                f"このファイルは既に処理されているようです:\n{output_file_path}\n上書きしますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                # 新しいファイル名を生成（連番を付加）
                base_path = os.path.splitext(output_file_path)[0]
                counter = 1
                while os.path.exists(f"{base_path}_{counter}.xlsx"):
                    counter += 1
                output_file_path = f"{base_path}_{counter}.xlsx"
        else:
            # 未処理のファイルだが同名の出力ファイルが存在する場合
            reply = QMessageBox.question(
                None,
                "確認",
                f"出力ファイルが既に存在します:\n{output_file_path}\n上書きしますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                # 新しいファイル名を生成（連番を付加）
                base_path = os.path.splitext(output_file_path)[0]
                counter = 1
                while os.path.exists(f"{base_path}_{counter}.xlsx"):
                    counter += 1
                output_file_path = f"{base_path}_{counter}.xlsx"

    try:
        # 共通の時間軸を作成
        start_time = max(time.min(), adjusted_time.min())
        end_time = min(time.max(), adjusted_time.max())

        # 時間間隔を計算（サンプリングレートに基づく）
        time_step = 1.0 / 1000  # 1000Hzの場合

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

        # グラフ画像をExcelファイルに追加
        workbook = load_workbook(output_file_path)
        sheet = workbook.create_sheet(title="Gravity Level Graph")
        img = Image(graph_path)
        sheet.add_image(img, "A1")
        workbook.save(output_file_path)

        QMessageBox.information(None, "保存完了", f"Gravity Levelデータとグラフが {output_file_path} に保存されました")
        return output_file_path
    except PermissionError:
        raise ValueError(f"{output_file_path} に書き込みできません。権限を確認してください。")
    except Exception as e:
        raise ValueError(f"データの保存中にエラーが発生しました: {e}")


def export_g_quality_data(g_quality_data, original_file_path):
    """
    G-quality解析の結果をエクスポートする
    """
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
    output_file_path = os.path.splitext(original_file_path)[0] + "_processed.xlsx"
    try:
        # 既存のExcelファイルを読み込むか、新規作成
        try:
            workbook = load_workbook(output_file_path)
        except FileNotFoundError:
            workbook = Workbook()
            workbook.remove(workbook.active)  # デフォルトのシートを削除

        # G-quality Analysis シートを作成または更新
        sheet_name = "G-quality Analysis"
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            for row in sheet[sheet.min_row : sheet.max_row]:  # シートをクリア
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
