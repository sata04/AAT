#!/usr/bin/env python3
"""
列選択ダイアログモジュール

CSVファイルからデータを読み込む際に、時間列と加速度列を選択するための
ダイアログウィジェットを提供します。
"""

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.logger import get_logger

# ロガーの初期化
logger = get_logger("column_selector_dialog")


class ColumnSelectorDialog(QDialog):
    """
    時間列と加速度列を選択するためのダイアログ

    CSVファイル内に複数の時間列や加速度列の候補がある場合に、
    ユーザーが適切な列を選択できるようにするUIを提供します。
    Inner CapsuleとDrag Shieldには異なる加速度列を選択する必要があります。
    """

    def __init__(self, time_columns, accel_columns, parent=None):
        """
        ColumnSelectorDialogのコンストラクタ

        Args:
            time_columns (list): 時間列の候補リスト
            accel_columns (list): 加速度列の候補リスト
            parent (QWidget, optional): 親ウィジェット。デフォルトはNone。
        """
        super().__init__(parent)

        self.time_columns = time_columns
        self.accel_columns = accel_columns

        self.setWindowTitle("データ列の選択")
        self.setMinimumWidth(500)  # 幅を広げて長い列名を表示しやすくする

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # 説明ラベル
        info_label = QLabel(
            "CSVファイル内に複数の時間列または加速度列候補があります。\n使用する列を選択してください。\n選択した列名はAcceleration dataの保存にも使用されます。"
        )
        self.main_layout.addWidget(info_label)

        # 時間列の選択
        time_layout = QHBoxLayout()
        time_label = QLabel("時間列:")
        self.time_combo = QComboBox()
        self.time_combo.addItems(self.time_columns)
        # ドロップダウンの幅を広げて長い列名を表示できるようにする
        self.time_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_combo)
        self.main_layout.addLayout(time_layout)

        # Inner Capsule 加速度列の選択
        inner_layout = QHBoxLayout()
        inner_label = QLabel("内カプセル加速度列 (Inner Capsule):")
        self.inner_combo = QComboBox()
        self.inner_combo.addItems(self.accel_columns)
        self.inner_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        inner_layout.addWidget(inner_label)
        inner_layout.addWidget(self.inner_combo)
        self.main_layout.addLayout(inner_layout)

        # Drag Shield 加速度列の選択
        drag_layout = QHBoxLayout()
        drag_label = QLabel("外カプセル加速度列 (Drag Shield):")
        self.drag_combo = QComboBox()
        self.drag_combo.addItems(self.accel_columns)
        self.drag_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        # 2つ以上の加速度列がある場合はインデックス1を選択（0とは異なる選択肢）
        if len(self.accel_columns) > 1:
            self.drag_combo.setCurrentIndex(1)
        drag_layout.addWidget(drag_label)
        drag_layout.addWidget(self.drag_combo)
        self.main_layout.addLayout(drag_layout)

        # ボタン
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(button_layout)

    def validate_and_accept(self):
        """
        選択が有効かを確認してダイアログを閉じる

        Inner CapsuleとDrag Shieldに同じ列が選択されていないか確認し、
        問題なければダイアログを受理します。
        """
        time_col = self.time_combo.currentText()
        inner_col = self.inner_combo.currentText()
        drag_col = self.drag_combo.currentText()

        # Inner CapsuleとDrag Shieldに同じ列が選択されていないか確認
        if inner_col == drag_col:
            QMessageBox.warning(
                self,
                "警告",
                "Inner CapsuleとDrag Shieldには異なる加速度列を選択してください。",
            )
            return

        # 選択が有効であればダイアログを閉じる
        logger.info(
            f"列選択: 時間列={time_col}, Inner Capsule={inner_col}, Drag Shield={drag_col}"
        )
        self.accept()

    def get_selected_columns(self):
        """
        選択された列名を返す

        Returns:
            tuple: (時間列, Inner Capsule加速度列, Drag Shield加速度列)
        """
        return (
            self.time_combo.currentText(),
            self.inner_combo.currentText(),
            self.drag_combo.currentText(),
        )
