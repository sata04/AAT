#!/usr/bin/env python3
"""
ロガーモジュール

アプリケーション全体で使用する統一的なロギング機能を提供します。
各モジュールは専用のロガーインスタンスを取得して使用できます。
"""

import logging

# グローバルロガーインスタンス
logger = logging.getLogger("AAT")


def get_logger(module_name):
    """
    指定したモジュール名のロガーを取得する

    モジュールごとに名前空間が分離されたロガーを提供し、
    ログの発生源を明確に識別できるようにします。

    Args:
        module_name (str): モジュール名

    Returns:
        logging.Logger: モジュール専用のロガーインスタンス
    """
    return logging.getLogger(f"AAT.{module_name}")


def log_exception(e, message="エラーが発生しました"):
    """
    例外情報をログに記録する

    統一的な形式で例外情報をエラーレベルでログに記録します。

    Args:
        e (Exception): 発生した例外
        message (str, optional): 追加のエラーメッセージ。デフォルトは「エラーが発生しました」。
    """
    logger.error(f"{message}: {str(e)}")
