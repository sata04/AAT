# core/data_processor.py
# データの読み込みと処理

import numpy as np
import pandas as pd


def load_and_process_data(file_path, config):
    """
    CSVファイルからデータを読み込み、処理する
    """
    try:
        data = pd.read_csv(file_path)
        time = data[config["time_column"]]
        acceleration_inner_capsule = data[config["acceleration_column_inner_capsule"]]
        acceleration_drag_shield = data[config["acceleration_column_drag_shield"]]

        # 加速度の閾値（デフォルト1m/s^2）を設定
        acceleration_threshold = config.get("acceleration_threshold", 1.0)

        # Drag Shieldの同期点を見つける
        sync_indices = np.where(np.abs(acceleration_drag_shield) < acceleration_threshold)[0]
        if len(sync_indices) > 0:
            sync_index = sync_indices[0]

            # inner_capsuleの時間はそのまま、drag_shieldの時間のみを調整
            adjusted_time = pd.Series(time - time.iloc[sync_index])

            gravity_level_inner_capsule = acceleration_inner_capsule / config["gravity_constant"]
            gravity_level_drag_shield = acceleration_drag_shield / config["gravity_constant"]

            return time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time
        else:
            raise ValueError("Drag Shieldの同期点が見つかりませんでした")
    except KeyError as e:
        raise ValueError(f"CSVファイルに必要な列がありません: {e}")
    except Exception as e:
        raise ValueError(f"データの読み込み中にエラーが発生しました: {e}")


def filter_data(time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time, config):
    """
    データをフィルタリングする
    """
    try:
        # それぞれのデータセットで独立して終了インデックスを計算
        end_index_inner = np.where(gravity_level_inner_capsule >= config["end_gravity_level"])[0]
        end_index_drag = np.where(gravity_level_drag_shield >= config["end_gravity_level"])[0]

        # データセットごとに個別の終了点を設定
        if len(end_index_inner) > 0:
            end_index_inner = end_index_inner[0]
        else:
            end_index_inner = len(gravity_level_inner_capsule) - 1

        if len(end_index_drag) > 0:
            end_index_drag = end_index_drag[0]
        else:
            end_index_drag = len(gravity_level_drag_shield) - 1

        # 開始点は0秒から
        start_index_inner = np.where(time >= 0)[0][0]
        start_index_drag = np.where(adjusted_time >= 0)[0][0]

        # データセットごとに個別にフィルタリング
        filtered_time = time[start_index_inner : end_index_inner + 1]
        filtered_gravity_level_inner_capsule = gravity_level_inner_capsule[start_index_inner : end_index_inner + 1]

        filtered_adjusted_time = adjusted_time[start_index_drag : end_index_drag + 1]
        filtered_gravity_level_drag_shield = gravity_level_drag_shield[start_index_drag : end_index_drag + 1]

        # 統計情報の計算のために全体の終了インデックスを保持
        end_index = max(end_index_inner, end_index_drag)

        return (filtered_time, filtered_gravity_level_inner_capsule, filtered_gravity_level_drag_shield, filtered_adjusted_time, end_index)

    except Exception as e:
        print(f"フィルタリング中にエラーが発生しました: {e}")
        return time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time, len(time) - 1
