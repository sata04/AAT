#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acceleration Analysis Tool (AAT)
微小重力環境下での実験データを分析するためのメインアプリケーション

このモジュールはアプリケーションのエントリーポイントです。
PyQt6ベースのGUIを起動し、CSVデータからの重力レベル分析を実行します。
"""

import os
import sys
import warnings

# macOS特有の警告を抑制
if sys.platform == "darwin":
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    # ウィンドウ移動に関する警告を無視
    warnings.filterwarnings("ignore", message=".*Window move completed without beginning.*")
    # TSM関連のエラーメッセージを標準エラー出力から除外
    os.environ["QT_MAC_WANTS_LAYER"] = "1"
    # 標準エラー出力をリダイレクト（オプション）
    if not os.environ.get("AAT_DEBUG"):
        sys.stderr = open(os.devnull, 'w')

from PyQt6.QtWidgets import QApplication, QMessageBox

from core.logger import get_logger, log_exception
from gui.main_window import MainWindow

# モジュール用のロガーを初期化
logger = get_logger("main")


def main():
    """
    アプリケーションのメインエントリーポイント

    Returns:
        int: アプリケーションの終了コード
    """
    try:
        logger.info("アプリケーションを起動します")
        app = QApplication(sys.argv)
        main_window = MainWindow()
        main_window.show()
        return app.exec()
    except Exception as e:
        log_exception(e, "アプリケーション実行中にエラーが発生しました")
        # ユーザーにもエラーを通知
        QMessageBox.critical(None, "エラー", f"予期せぬエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
