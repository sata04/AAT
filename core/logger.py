#!/usr/bin/env python3
"""
ロガーモジュール

アプリケーション全体で使用する統一的なロギング機能を提供します。
各モジュールは専用のロガーインスタンスを取得して使用できます。
"""

import logging
import os
import sys


# ロギングの基本設定
def _setup_logging() -> None:
    """ロギングシステムの初期化"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # ログレベルを環境変数またはコマンドライン引数から取得
    # デフォルトはWARNINGレベル（重要なメッセージのみ表示）
    log_level = logging.WARNING

    # 環境変数AAT_LOG_LEVELでログレベルを設定
    log_level_env = os.environ.get("AAT_LOG_LEVEL")
    if log_level_env:
        log_level_str = log_level_env.upper()
        log_level = getattr(logging, log_level_str, logging.WARNING)

    # デバッグモードの場合はDEBUGレベル
    if os.environ.get("AAT_DEBUG") or "--debug" in sys.argv:
        log_level = logging.DEBUG
    # 詳細モードの場合はINFOレベル
    elif "--verbose" in sys.argv or "-v" in sys.argv:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


# ロギングシステムを初期化
_setup_logging()

# グローバルロガーインスタンス
logger: logging.Logger = logging.getLogger("AAT")


def get_logger(module_name: str) -> logging.Logger:
    """
    指定したモジュール名のロガーを取得する

    モジュールごとに名前空間が分離されたロガーを提供し、
    ログの発生源を明確に識別できるようにします。

    Args:
        module_name: モジュール名

    Returns:
        モジュール専用のロガーインスタンス
    """
    return logging.getLogger(f"AAT.{module_name}")


def log_exception(e: Exception, message: str = "エラーが発生しました") -> None:
    """
    例外情報をログに記録する

    統一的な形式で例外情報をエラーレベルでログに記録します。

    Args:
        e: 発生した例外
        message: 追加のエラーメッセージ。デフォルトは「エラーが発生しました」。
    """
    logger.error(f"{message}: {str(e)}", exc_info=True)
