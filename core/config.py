#!/usr/bin/env python3
"""
設定管理モジュール

アプリケーション全体の設定を管理します。JSONファイルからの読み込み、
デフォルト値の提供、および設定の保存機能を提供します。
"""

import json
import shutil
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QMessageBox

from core.logger import get_logger, log_exception

# ロガーの初期化
logger = get_logger("config")

# アプリケーションのバージョン情報
APP_VERSION: str = "9.2.0"


def load_config() -> dict[str, Any]:
    """
    設定ファイルを読み込む

    1. config/config.default.jsonからデフォルト設定を読み込み
    2. config.jsonからユーザー設定を読み込み（存在する場合）
    3. ユーザー設定が存在しない場合は、デフォルト設定をコピーして作成

    Returns:
        dict: 設定情報を含む辞書
    """
    script_dir = Path(__file__).resolve().parent.parent
    default_config_path = script_dir / "config" / "config.default.json"
    user_config_path = script_dir / "config.json"

    logger.debug(f"デフォルト設定ファイルのパス: {default_config_path}")
    logger.debug(f"ユーザー設定ファイルのパス: {user_config_path}")

    # デフォルト設定を読み込み
    try:
        with default_config_path.open("r", encoding="utf-8") as f:
            logger.info("デフォルト設定ファイルを読み込んでいます")
            default_config = json.load(f)
            logger.debug(f"読み込まれたデフォルト設定: {default_config}")
    except FileNotFoundError:
        logger.error(f"デフォルト設定ファイルが見つかりません: {default_config_path}")
        # フォールバック用のハードコードされたデフォルト設定
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
            "g_quality_end": 0.5,
            "g_quality_step": 0.05,
            "min_seconds_after_start": 0.0,
            "auto_calculate_g_quality": True,
            "use_cache": True,
            "default_graph_duration": 1.45,
            "app_version": APP_VERSION,
        }
    except json.JSONDecodeError as e:
        logger.error(f"デフォルト設定ファイルの解析に失敗しました: {e}")
        raise

    # バージョン情報は常に最新を使用
    default_config["app_version"] = APP_VERSION

    # ユーザー設定ファイルが存在するかチェック
    if not user_config_path.exists():
        logger.info("ユーザー設定ファイルが存在しません。デフォルト設定をコピーします")
        try:
            shutil.copy2(default_config_path, user_config_path)
            logger.info(f"デフォルト設定をユーザー設定としてコピーしました: {user_config_path}")
        except Exception as e:
            logger.warning(f"ユーザー設定ファイルの作成に失敗しました: {e}")

    # ユーザー設定を読み込み
    try:
        with user_config_path.open("r", encoding="utf-8") as f:
            logger.info("ユーザー設定ファイルを読み込んでいます")
            user_config = json.load(f)
            logger.debug(f"読み込まれたユーザー設定: {user_config}")

        # ユーザー設定でデフォルト設定を上書き
        for key in default_config:
            if key in user_config:
                default_config[key] = user_config[key]

        # バージョン情報は常に最新を使用
        default_config["app_version"] = APP_VERSION

        logger.info("設定ファイルの読み込みに成功しました")
    except FileNotFoundError:
        logger.warning(f"ユーザー設定ファイルが見つかりません: {user_config_path}")
        logger.info("デフォルト設定を使用します")
    except json.JSONDecodeError as e:
        logger.error(f"ユーザー設定ファイルの解析に失敗しました: {e}")
        QMessageBox.warning(
            None,
            "設定ファイルエラー",
            f"ユーザー設定ファイルの解析に失敗しました: {user_config_path}\nデフォルト設定を使用します。",
        )

    logger.debug(f"最終的な設定: {default_config}")
    return default_config


def save_config(config: dict[str, Any]) -> bool:
    """
    設定ファイルを保存する

    指定された設定情報をJSONファイルに保存します。
    エラー時は既存の設定を保護するためにバックアップを作成します。

    Args:
        config (dict): 保存する設定情報

    Returns:
        bool: 保存に成功した場合はTrue、失敗した場合はFalse
    """
    script_dir = Path(__file__).resolve().parent.parent
    config_path = script_dir / "config.json"
    backup_path = script_dir / "config.json.bak"

    logger.debug(f"設定を保存します: {config}")

    try:
        # 既存の設定ファイルがあればバックアップ
        if config_path.exists():
            shutil.copy2(config_path, backup_path)
            logger.debug(f"設定ファイルをバックアップしました: {backup_path}")

        # 浮動小数点精度問題を修正するため、JSON文字列を処理
        config_str = json.dumps(config, indent=4, ensure_ascii=False)
        # 浮動小数点の精度問題を修正
        config_str = config_str.replace("0.6800000000000002", "0.68")

        with config_path.open("w", encoding="utf-8") as f:
            f.write(config_str)
        logger.info(f"設定ファイルを正常に保存しました: {config_path}")
        return True
    except Exception as e:
        log_exception(e, "設定の保存中にエラーが発生しました")

        # バックアップから復元を試みる
        if backup_path.exists():
            try:
                shutil.copy2(backup_path, config_path)
                logger.info(f"バックアップから設定を復元しました: {backup_path}")
            except Exception as e2:
                log_exception(e2, "バックアップからの復元に失敗しました")

        QMessageBox.warning(None, "設定保存エラー", f"設定の保存中にエラーが発生しました: {e}")
        return False
