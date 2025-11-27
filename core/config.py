#!/usr/bin/env python3
"""
設定管理モジュール

アプリケーション全体の設定を管理します。JSONファイルからの読み込み、
デフォルト値の提供、および設定の保存機能を提供します。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from core.logger import get_logger, log_exception
from core.version import APP_VERSION

# ロガーの初期化
logger = get_logger("config")


def _get_app_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def _default_user_config_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AAT"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "AAT"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "AAT"


def get_user_config_dir() -> Path:
    override_dir = os.environ.get("AAT_CONFIG_DIR")
    base_dir = Path(override_dir).expanduser() if override_dir else _default_user_config_dir()
    if override_dir:
        logger.debug("環境変数AAT_CONFIG_DIRでユーザー設定ディレクトリを指定: %s", base_dir)

    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # pragma: no cover - 予期しないパスや権限のためのフォールバック
        logger.warning("ユーザー設定ディレクトリの作成に失敗しました (%s)。ホーム直下に退避します。", exc)
        fallback_dir = Path.home() / ".AAT"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir

    return base_dir


def _migrate_legacy_config(user_config_path: Path, backup_path: Path) -> None:
    legacy_dir = _get_app_root()
    legacy_config_path = legacy_dir / "config.json"
    legacy_backup_path = legacy_dir / "config.json.bak"

    if user_config_path.exists() or not legacy_config_path.exists():
        return

    logger.info("旧形式の設定ファイルが見つかりました。新しい保存場所へ移動します: %s", legacy_config_path)
    try:
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy_config_path), user_config_path)
        logger.info("設定ファイルを移動しました: %s -> %s", legacy_config_path, user_config_path)

        if legacy_backup_path.exists() and not backup_path.exists():
            shutil.move(str(legacy_backup_path), backup_path)
            logger.info("バックアップファイルも移動しました: %s -> %s", legacy_backup_path, backup_path)
    except Exception as exc:  # pragma: no cover
        logger.warning("旧設定ファイルの移行に失敗しました: %s", exc)


def load_config(on_warning: Callable[[str], None] | None = None) -> dict[str, Any]:
    """
    設定ファイルを読み込む

    1. config/config.default.jsonからデフォルト設定を読み込み
    2. ユーザー設定ディレクトリ（環境変数AAT_CONFIG_DIRで上書き可）のconfig.jsonを読み込み
    3. ユーザー設定が存在しない場合は、デフォルト設定をコピーして作成
       旧仕様のconfig.jsonがアプリケーションルートにある場合は自動で移行

    Returns:
        dict: 設定情報を含む辞書
    """
    warn = on_warning or (lambda msg: logger.warning("%s", msg))

    app_root = _get_app_root()
    default_config_path = app_root / "config" / "config.default.json"

    user_config_dir = get_user_config_dir()
    user_config_path = user_config_dir / "config.json"
    backup_path = user_config_dir / "config.json.bak"

    _migrate_legacy_config(user_config_path, backup_path)

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
            "use_inner_acceleration": True,
            "use_drag_acceleration": True,
            "sampling_rate": 1000,
            "gravity_constant": 9.797578,
            "ylim_min": -1.0,
            "ylim_max": 1.0,
            "acceleration_threshold": 5.0,
            "end_gravity_level": 8.0,
            "window_size": 0.1,
            "g_quality_start": 0.1,
            "g_quality_end": 1.0,
            "g_quality_step": 0.05,
            "min_seconds_after_start": 0.7,
            "auto_calculate_g_quality": True,
            "use_cache": True,
            "default_graph_duration": 1.45,
            "graph_sensor_mode": "both",
            "theme": "system",
            "export_figure_width": 10.6,
            "export_figure_height": 3.4,
            "export_dpi": 300,
            "export_bbox_inches": None,
            "invert_inner_acceleration": True,
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
            user_config_dir.mkdir(parents=True, exist_ok=True)
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
        warn(f"ユーザー設定ファイルの解析に失敗しました: {user_config_path}\nデフォルト設定を使用します。")

    logger.debug(f"最終的な設定: {default_config}")
    return default_config


def save_config(config: dict[str, Any], on_error: Callable[[str], None] | None = None) -> bool:
    """
    設定ファイルを保存する

    指定された設定情報をJSONファイルに保存します。
    エラー時は既存の設定を保護するためにバックアップを作成します。

    Args:
        config (dict): 保存する設定情報

    Returns:
        bool: 保存に成功した場合はTrue、失敗した場合はFalse
    """
    notify_error = on_error or (lambda msg: logger.warning("%s", msg))

    user_config_dir = get_user_config_dir()
    config_path = user_config_dir / "config.json"
    backup_path = user_config_dir / "config.json.bak"

    user_config_dir.mkdir(parents=True, exist_ok=True)

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

        notify_error(f"設定の保存中にエラーが発生しました: {e}")
        return False
