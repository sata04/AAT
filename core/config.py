#!/usr/bin/env python3
"""
設定管理モジュール

アプリケーション全体の設定を管理します。JSONファイルからの読み込み、
デフォルト値の提供、および設定の保存機能を提供します。
"""

import json
import os

from PyQt6.QtWidgets import QMessageBox

from core.logger import get_logger, log_exception

# ロガーの初期化
logger = get_logger("config")

# アプリケーションのバージョン情報
APP_VERSION = "9.1.0"


def load_config():
    """
    設定ファイルを読み込む

    config.jsonファイルから設定を読み込みます。ファイルが存在しない場合や
    解析エラーが発生した場合はデフォルト設定を使用します。

    ユーザー設定が存在する場合はデフォルト設定を上書きします。

    Returns:
        dict: 設定情報を含む辞書
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
        "min_seconds_after_start": 0.0,  # 開始点からの最小秒数（デフォルトは0秒）
        "auto_calculate_g_quality": True,  # ファイル読み込み時にG-quality評価を自動計算
        "use_cache": True,  # 処理済みデータのキャッシュを使用するかどうか
        "app_version": APP_VERSION,  # アプリケーションバージョン
    }
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(script_dir, "config.json")
    logger.debug(f"設定ファイルのパス: {config_path}")

    try:
        with open(config_path) as f:
            logger.info("設定ファイルを読み込んでいます")
            user_config = json.load(f)
            logger.debug(f"読み込まれた設定: {user_config}")

        # 設定ファイルの値でデフォルト値を更新するが、存在しないキーはデフォルト値のまま
        for key in default_config:
            if key in user_config:
                default_config[key] = user_config[key]

        # バージョン情報は常に最新を使用
        default_config["app_version"] = APP_VERSION

        logger.info("設定ファイルの読み込みに成功しました")
    except FileNotFoundError:
        logger.warning(f"設定ファイルが見つかりません: {config_path}")
        QMessageBox.warning(
            None,
            "設定ファイルエラー",
            f"設定ファイルが見つかりません: {config_path}\nデフォルト設定を使用します。",
        )
    except json.JSONDecodeError as e:
        logger.error(f"設定ファイルの解析に失敗しました: {e}")
        QMessageBox.warning(
            None,
            "設定ファイルエラー",
            f"設定ファイルの解析に失敗しました: {config_path}\nデフォルト設定を使用します。",
        )

    logger.debug(f"最終的な設定: {default_config}")
    return default_config


def save_config(config):
    """
    設定ファイルを保存する

    指定された設定情報をJSONファイルに保存します。
    エラー時は既存の設定を保護するためにバックアップを作成します。

    Args:
        config (dict): 保存する設定情報

    Returns:
        bool: 保存に成功した場合はTrue、失敗した場合はFalse
    """
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(script_dir, "config.json")
    backup_path = os.path.join(script_dir, "config.json.bak")

    logger.debug(f"設定を保存します: {config}")

    try:
        # 既存の設定ファイルがあればバックアップ
        if os.path.exists(config_path):
            import shutil

            shutil.copy2(config_path, backup_path)
            logger.debug(f"設定ファイルをバックアップしました: {backup_path}")

        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        logger.info(f"設定ファイルを正常に保存しました: {config_path}")
        return True
    except Exception as e:
        log_exception(e, "設定の保存中にエラーが発生しました")

        # バックアップから復元を試みる
        if os.path.exists(backup_path):
            try:
                import shutil

                shutil.copy2(backup_path, config_path)
                logger.info(f"バックアップから設定を復元しました: {backup_path}")
            except Exception as e2:
                log_exception(e2, "バックアップからの復元に失敗しました")

        QMessageBox.warning(None, "設定保存エラー", f"設定の保存中にエラーが発生しました: {e}")
        return False
