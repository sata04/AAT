# core/config.py
# 設定関連の機能

import json
import os

from PyQt6.QtWidgets import QMessageBox


def load_config():
    """
    設定ファイルを読み込む
    """
    default_config = {
        "time_column": "データセット1:時間(s)",
        "acceleration_column_inner_capsule": "データセット1:Z-axis acceleration 1(m/s²)",
        "acceleration_column_drag_shield": "データセット1:Z-axis acceleration 2(m/s²)",
        "sampling_rate": 1000,
        "gravity_constant": 9.797578,
        "ylim_min": -1,
        "ylim_max": 1,
        "acceleration_threshold": 1.0,
        "end_gravity_level": 8,
        "window_size": 0.1,
        "g_quality_start": 0.1,
        "g_quality_end": 1.0,
        "g_quality_step": 0.05,
    }
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(script_dir, "config.json")
    try:
        with open(config_path, "r") as f:
            user_config = json.load(f)
        # 設定ファイルの値でデフォルト値を更新するが、存在しないキーはデフォルト値のまま
        for key in default_config:
            if key in user_config:
                default_config[key] = user_config[key]
    except FileNotFoundError:
        QMessageBox.warning(None, "設定ファイルエラー", f"設定ファイルが見つかりません: {config_path}\nデフォルト設定を使用します。")
    except json.JSONDecodeError:
        QMessageBox.warning(None, "設定ファイルエラー", f"設定ファイルの解析に失敗しました: {config_path}\nデフォルト設定を使用します。")
    return default_config


def save_config(config):
    """
    設定ファイルを保存する
    """
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(script_dir, "config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        QMessageBox.warning(None, "設定保存エラー", f"設定の保存中にエラーが発生しました: {e}")
        return False
