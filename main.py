#!/usr/bin/env python3
"""
Acceleration Analysis Tool (AAT)
微小重力環境下での実験データを分析するためのメインアプリケーション

このモジュールはアプリケーションのエントリーポイントです。
PyQt6ベースのGUIを起動し、CSVデータからの重力レベル分析を実行します。
"""

import os
import signal
import sys
import traceback
import warnings

# macOS特有の警告を抑制
if sys.platform == "darwin":
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    # ウィンドウ移動に関する警告を無視
    warnings.filterwarnings("ignore", message=".*Window move completed without beginning.*")
    # TSM関連のエラーメッセージを標準エラー出力から除外
    os.environ["QT_MAC_WANTS_LAYER"] = "1"
    # 標準エラー出力のリダイレクト（クラッシュ時のデバッグ情報を保持）
    if not os.environ.get("AAT_DEBUG"):
        # 重要なエラー情報は保持し、Qt関連の警告のみを抑制
        import atexit
        import io

        # オリジナルのstderrを保存
        original_stderr = sys.stderr

        # フィルタリング用のライター
        class FilteredStderr:
            def __init__(self, original):
                self.original = original
                self.buffer = io.StringIO()

            def write(self, data):
                # クラッシュやセグメンテーション違反の情報は出力
                if any(
                    keyword in data.lower()
                    for keyword in ["abort", "segmentation", "fatal", "crash", "exception", "error", "traceback"]
                ) or not any(keyword in data.lower() for keyword in ["qt.qpa", "tsm", "window move", "qtwarning"]):
                    self.original.write(data)
                    self.original.flush()

            def flush(self):
                self.original.flush()

            def fileno(self):
                return self.original.fileno()

        sys.stderr = FilteredStderr(original_stderr)

        # プログラム終了時にstderrを復元
        atexit.register(lambda: setattr(sys, "stderr", original_stderr))

from PyQt6.QtWidgets import QApplication, QMessageBox

from core.logger import get_logger, log_exception
from gui.main_window import MainWindow

# モジュール用のロガーを初期化
logger = get_logger("main")


def handle_crash(signum, frame):
    """
    クラッシュシグナルのハンドラー

    Args:
        signum: シグナル番号
        frame: フレームオブジェクト
    """
    logger.error(f"クラッシュシグナルを受信しました: {signum}")
    traceback.print_stack(frame)
    sys.exit(1)


def main():
    """
    アプリケーションのメインエントリーポイント

    Returns:
        int: アプリケーションの終了コード
    """
    # クラッシュシグナルのハンドラーを設定
    if sys.platform == "darwin":
        signal.signal(signal.SIGABRT, handle_crash)
        signal.signal(signal.SIGSEGV, handle_crash)
        signal.signal(signal.SIGBUS, handle_crash)

    try:
        logger.info("アプリケーションを起動します")

        # QApplicationの作成前にQtの設定を確認
        if sys.platform == "darwin":
            os.environ.setdefault("QT_MAC_WANTS_LAYER", "1")
            os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

        app = QApplication(sys.argv)

        # アプリケーション設定
        app.setApplicationName("AAT")
        app.setApplicationVersion("9.3.0")
        app.setOrganizationName("AAT Development Team")

        logger.info("MainWindowを作成します")
        main_window = MainWindow()
        main_window.show()

        logger.info("アプリケーションループを開始します")
        result = app.exec()
        logger.info(f"アプリケーションが終了しました (終了コード: {result})")
        return result

    except Exception as e:
        logger.error(f"アプリケーション実行中にエラーが発生しました: {e}")
        log_exception(e, "アプリケーション実行中にエラーが発生しました")

        # デバッグ情報を出力
        traceback.print_exc()

        try:
            # ユーザーにもエラーを通知（QApplicationが作成済みの場合のみ）
            if "app" in locals():
                QMessageBox.critical(None, "エラー", f"予期せぬエラーが発生しました: {e}")
        except Exception:
            # QApplicationが作成されていない場合はログのみ
            pass

        return 1


if __name__ == "__main__":
    sys.exit(main())
