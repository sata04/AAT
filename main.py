# main.py
# 重力レベル分析ツールのメインエントリーポイント

import os
import sys

# macOS特有のIMKエラーメッセージを抑制
if sys.platform == "darwin":
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main():
    """
    アプリケーションのメインエントリーポイント
    """
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


# プログラムのエントリーポイント
if __name__ == "__main__":
    main()
