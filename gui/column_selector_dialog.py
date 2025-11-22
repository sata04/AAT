#!/usr/bin/env python3
"""
列選択ダイアログモジュール

CSVファイルからデータを読み込む際に、時間列と加速度列を選択するための
ダイアログウィジェットを提供します。
"""

from PySide6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from core.logger import get_logger
from gui.widgets import ToggleSwitch

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
        self.setMinimumWidth(600)

        # メインレイアウト
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(24)
        self.setLayout(self.main_layout)

        # 説明ラベル
        if len(accel_columns) == 1:
            info_text = (
                "加速度データが1系列だけ見つかりました。\n"
                "時間列を選び、どのセンサーを使用するか確認してください。\n"
                "Drag Shieldはデータ未検出のため初期状態で無効にしています。"
            )
        else:
            info_text = (
                "CSVファイル内に複数の時間列または加速度列候補があります。\n"
                "使用する列を選択してください。\n"
                "選択した列名はAcceleration dataの保存にも使用されます。"
            )
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        self.main_layout.addWidget(info_label)

        # フォームレイアウト
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)

        # 時間列の選択
        time_group = QVBoxLayout()
        time_group.setSpacing(8)
        time_label = QLabel("時間列:")
        time_label.setStyleSheet("font-weight: bold;")
        self.time_combo = QComboBox()
        self.time_combo.addItems(self.time_columns)
        self.time_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        time_group.addWidget(time_label)
        time_group.addWidget(self.time_combo)
        form_layout.addLayout(time_group)

        # Inner Capsule 加速度列の選択
        inner_group = QVBoxLayout()
        inner_group.setSpacing(8)
        inner_label = QLabel("内カプセル加速度列 (Inner Capsule):")
        inner_label.setStyleSheet("font-weight: bold;")
        self.use_inner_toggle = ToggleSwitch()
        self.use_inner_toggle.setChecked(True)
        inner_toggle_row = QHBoxLayout()
        inner_toggle_row.setSpacing(8)
        inner_toggle_label = QLabel("Inner Capsule のデータを使用する")
        inner_toggle_row.addWidget(inner_toggle_label)
        inner_toggle_row.addStretch()
        inner_toggle_row.addWidget(self.use_inner_toggle)
        self.inner_combo = QComboBox()
        self.inner_combo.addItems(self.accel_columns)
        self.inner_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        inner_group.addWidget(inner_label)
        inner_group.addLayout(inner_toggle_row)
        inner_group.addWidget(self.inner_combo)
        self.inner_combo.setEnabled(self.use_inner_toggle.isChecked())
        form_layout.addLayout(inner_group)

        # Drag Shield 加速度列の選択
        drag_group = QVBoxLayout()
        drag_group.setSpacing(8)
        drag_label = QLabel("外カプセル加速度列 (Drag Shield):")
        drag_label.setStyleSheet("font-weight: bold;")
        default_use_drag = len(self.accel_columns) > 1
        self.use_drag_toggle = ToggleSwitch()
        self.use_drag_toggle.setChecked(default_use_drag)
        drag_toggle_row = QHBoxLayout()
        drag_toggle_row.setSpacing(8)
        drag_toggle_label = QLabel("Drag Shield のデータを使用する")
        drag_toggle_row.addWidget(drag_toggle_label)
        drag_toggle_row.addStretch()
        drag_toggle_row.addWidget(self.use_drag_toggle)
        self.drag_combo = QComboBox()
        self.drag_combo.addItems(self.accel_columns)
        self.drag_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        # 2つ以上の加速度列がある場合はインデックス1を選択（0とは異なる選択肢）
        if len(self.accel_columns) > 1:
            self.drag_combo.setCurrentIndex(1)
        else:
            self.drag_combo.setEnabled(default_use_drag)
        drag_group.addWidget(drag_label)
        drag_group.addLayout(drag_toggle_row)
        drag_group.addWidget(self.drag_combo)
        self.drag_combo.setEnabled(self.use_drag_toggle.isChecked())
        form_layout.addLayout(drag_group)

        # チェックボックスとコンボの連動
        self.use_inner_toggle.toggled.connect(self.inner_combo.setEnabled)
        self.use_drag_toggle.toggled.connect(self.drag_combo.setEnabled)

        self.main_layout.addLayout(form_layout)
        self.main_layout.addStretch()

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.setObjectName("Secondary")
        self.cancel_button.clicked.connect(self.reject)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.validate_and_accept)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
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
        use_inner = self.use_inner_toggle.isChecked()
        use_drag = self.use_drag_toggle.isChecked()

        if not use_inner and not use_drag:
            QMessageBox.warning(
                self,
                "警告",
                "Inner CapsuleとDrag Shieldのどちらか一方は有効にしてください。",
            )
            return

        # Inner CapsuleとDrag Shieldに同じ列が選択されていないか確認
        if use_inner and use_drag and inner_col == drag_col:
            QMessageBox.warning(
                self,
                "警告",
                "Inner CapsuleとDrag Shieldには異なる加速度列を選択してください。",
            )
            return

        # 選択が有効であればダイアログを閉じる
        logger.info(
            f"列選択: 時間列={time_col}, Inner Capsule={inner_col if use_inner else '未使用'}, "
            f"Drag Shield={drag_col if use_drag else '未使用'}"
        )
        self.accept()

    def get_selected_columns(self):
        """
        選択された列名を返す

        Returns:
            tuple: (時間列, Inner Capsule加速度列 or None, Drag Shield加速度列 or None, use_inner, use_drag)
        """
        return (
            self.time_combo.currentText(),
            self.inner_combo.currentText() if self.use_inner_toggle.isChecked() else None,
            self.drag_combo.currentText() if self.use_drag_toggle.isChecked() else None,
            self.use_inner_toggle.isChecked(),
            self.use_drag_toggle.isChecked(),
        )
