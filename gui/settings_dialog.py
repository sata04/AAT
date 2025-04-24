# gui/settings_dialog.py
# 設定ダイアログ

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLineEdit, QSpinBox, QVBoxLayout


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("設定")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # 各設定項目のウィジェットを作成
        self.time_column = QLineEdit(self.config["time_column"])
        form_layout.addRow("時間列:", self.time_column)

        self.acceleration_column_inner_capsule = QLineEdit(self.config["acceleration_column_inner_capsule"])
        form_layout.addRow("加速度列 (Inner Capsule):", self.acceleration_column_inner_capsule)

        self.acceleration_column_drag_shield = QLineEdit(self.config["acceleration_column_drag_shield"])
        form_layout.addRow("加速度列 (Drag Shield):", self.acceleration_column_drag_shield)

        self.sampling_rate = QSpinBox()
        self.sampling_rate.setRange(1, 10000)
        self.sampling_rate.setValue(self.config["sampling_rate"])
        form_layout.addRow("サンプリングレート:", self.sampling_rate)

        self.gravity_constant = QDoubleSpinBox()
        self.gravity_constant.setRange(0, 100)
        self.gravity_constant.setDecimals(5)
        self.gravity_constant.setValue(self.config["gravity_constant"])
        form_layout.addRow("重力定数:", self.gravity_constant)

        self.ylim_min = QDoubleSpinBox()
        self.ylim_min.setRange(-100, 100)
        self.ylim_min.setValue(self.config["ylim_min"])
        form_layout.addRow("Y軸最小値:", self.ylim_min)

        self.ylim_max = QDoubleSpinBox()
        self.ylim_max.setRange(-100, 100)
        self.ylim_max.setValue(self.config["ylim_max"])
        form_layout.addRow("Y軸最大値:", self.ylim_max)

        self.acceleration_threshold = QDoubleSpinBox()
        self.acceleration_threshold.setRange(0, 10)
        self.acceleration_threshold.setDecimals(3)
        self.acceleration_threshold.setValue(self.config.get("acceleration_threshold", 1.0))
        form_layout.addRow("加速度同期閾値 (m/s²):", self.acceleration_threshold)

        self.end_gravity_level = QDoubleSpinBox()
        self.end_gravity_level.setRange(0, 100)
        self.end_gravity_level.setValue(self.config["end_gravity_level"])
        form_layout.addRow("終了Gravity_Level:", self.end_gravity_level)

        self.window_size = QDoubleSpinBox()
        self.window_size.setRange(0, 10)
        self.window_size.setDecimals(3)
        self.window_size.setValue(self.config["window_size"])
        form_layout.addRow("ウィンドウサイズ(s):", self.window_size)

        self.g_quality_start = QDoubleSpinBox()
        self.g_quality_start.setRange(0, 10)
        self.g_quality_start.setDecimals(2)
        self.g_quality_start.setValue(self.config["g_quality_start"])
        form_layout.addRow("G-quality評価開始値:", self.g_quality_start)

        self.g_quality_end = QDoubleSpinBox()
        self.g_quality_end.setRange(0, 10)
        self.g_quality_end.setDecimals(2)
        self.g_quality_end.setValue(self.config["g_quality_end"])
        form_layout.addRow("G-quality評価終了値:", self.g_quality_end)

        self.g_quality_step = QDoubleSpinBox()
        self.g_quality_step.setRange(0, 1)
        self.g_quality_step.setDecimals(3)
        self.g_quality_step.setValue(self.config["g_quality_step"])
        form_layout.addRow("G-quality評価ステップ:", self.g_quality_step)

        layout.addLayout(form_layout)

        # OKとキャンセルボタンを追加
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, Qt.Orientation.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self):
        """
        現在の設定値を取得する
        """
        return {
            "time_column": self.time_column.text(),
            "acceleration_column_inner_capsule": self.acceleration_column_inner_capsule.text(),
            "acceleration_column_drag_shield": self.acceleration_column_drag_shield.text(),
            "sampling_rate": self.sampling_rate.value(),
            "gravity_constant": self.gravity_constant.value(),
            "ylim_min": self.ylim_min.value(),
            "ylim_max": self.ylim_max.value(),
            "acceleration_threshold": self.acceleration_threshold.value(),
            "end_gravity_level": self.end_gravity_level.value(),
            "window_size": self.window_size.value(),
            "g_quality_start": self.g_quality_start.value(),
            "g_quality_end": self.g_quality_end.value(),
            "g_quality_step": self.g_quality_step.value(),
        }
