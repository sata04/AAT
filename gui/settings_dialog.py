#!/usr/bin/env python3
"""
設定ダイアログモジュール

アプリケーションの設定パラメータを編集するためのダイアログUIを提供します。
ユーザーが重力レベル解析に関連する様々なパラメータを調整できるようにします。
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from core.logger import get_logger

# ロガーの初期化
logger = get_logger("settings_dialog")


class SettingsDialog(QDialog):
    """
    アプリケーション設定を編集するダイアログ

    データ列の指定、サンプリングレート、重力定数、グラフ範囲、
    加速度閾値、終了重力レベル、解析ウィンドウサイズなど
    多様な設定パラメータを編集するインターフェースを提供します。
    """

    def __init__(self, config, parent=None):
        """
        設定ダイアログのコンストラクタ

        Args:
            config (dict): 現在の設定データ
            parent (QWidget, optional): 親ウィジェット。デフォルトはNone。
        """
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("設定")
        self.setModal(True)

        # レイアウトの初期化
        self._init_layout()

        logger.debug("設定ダイアログを初期化しました")

    def _init_layout(self):
        """
        ダイアログのレイアウトとウィジェットを初期化する
        """
        layout = QVBoxLayout(self)

        # データ入力設定グループ
        input_group = QGroupBox("データ入力設定")
        form_layout1 = QFormLayout(input_group)

        # データ列設定
        self.time_column = QLineEdit(self.config["time_column"])
        form_layout1.addRow("時間列:", self.time_column)

        self.acceleration_column_inner_capsule = QLineEdit(self.config["acceleration_column_inner_capsule"])
        form_layout1.addRow("加速度列 (Inner Capsule):", self.acceleration_column_inner_capsule)

        self.acceleration_column_drag_shield = QLineEdit(self.config["acceleration_column_drag_shield"])
        form_layout1.addRow("加速度列 (Drag Shield):", self.acceleration_column_drag_shield)

        # サンプリングレート設定
        self.sampling_rate = QSpinBox()
        self.sampling_rate.setRange(1, 10000)
        self.sampling_rate.setValue(self.config["sampling_rate"])
        form_layout1.addRow("サンプリングレート (Hz):", self.sampling_rate)

        # 重力定数
        self.gravity_constant = QDoubleSpinBox()
        self.gravity_constant.setRange(9.0, 10.0)
        self.gravity_constant.setDecimals(6)
        self.gravity_constant.setSingleStep(0.000001)
        self.gravity_constant.setValue(self.config["gravity_constant"])
        form_layout1.addRow("重力定数 (m/s²):", self.gravity_constant)

        # Inner加速度計の上下反転補正
        self.invert_inner_acceleration = QCheckBox()
        self.invert_inner_acceleration.setChecked(self.config.get("invert_inner_acceleration", False))
        form_layout1.addRow("Inner加速度計の上下反転補正:", self.invert_inner_acceleration)

        # パフォーマンス設定グループ
        perf_group = QGroupBox("パフォーマンス設定")
        perf_layout = QFormLayout(perf_group)

        # キャッシュ使用設定
        self.use_cache = QCheckBox()
        self.use_cache.setChecked(self.config.get("use_cache", True))
        perf_layout.addRow("処理済みデータをキャッシュする:", self.use_cache)

        # 自動G-quality評価
        self.auto_calculate_g_quality = QCheckBox()
        self.auto_calculate_g_quality.setChecked(self.config.get("auto_calculate_g_quality", True))
        perf_layout.addRow(
            "ファイル読み込み時にG-quality評価を自動計算:",
            self.auto_calculate_g_quality,
        )

        # グラフ表示設定グループ
        display_group = QGroupBox("グラフ表示設定")
        form_layout2 = QFormLayout(display_group)

        # グラフY軸範囲
        self.ylim_min = QDoubleSpinBox()
        self.ylim_min.setRange(-10.0, 10.0)
        self.ylim_min.setDecimals(2)
        self.ylim_min.setSingleStep(0.1)
        self.ylim_min.setValue(self.config["ylim_min"])
        form_layout2.addRow("グラフY軸最小値:", self.ylim_min)

        self.ylim_max = QDoubleSpinBox()
        self.ylim_max.setRange(-10.0, 10.0)
        self.ylim_max.setDecimals(2)
        self.ylim_max.setSingleStep(0.1)
        self.ylim_max.setValue(self.config["ylim_max"])
        form_layout2.addRow("グラフY軸最大値:", self.ylim_max)

        # デフォルトグラフ表示時間
        self.default_graph_duration = QDoubleSpinBox()
        self.default_graph_duration.setRange(0.1, 10.0)
        self.default_graph_duration.setDecimals(2)
        self.default_graph_duration.setSingleStep(0.05)
        self.default_graph_duration.setValue(self.config.get("default_graph_duration", 1.45))
        form_layout2.addRow("デフォルトグラフ表示時間 (秒):", self.default_graph_duration)

        # 解析設定グループ
        analysis_group = QGroupBox("解析設定")
        form_layout3 = QFormLayout(analysis_group)

        # 加速度閾値
        self.acceleration_threshold = QDoubleSpinBox()
        self.acceleration_threshold.setRange(0.01, 10.0)
        self.acceleration_threshold.setDecimals(2)
        self.acceleration_threshold.setSingleStep(0.1)
        self.acceleration_threshold.setValue(self.config["acceleration_threshold"])
        form_layout3.addRow("加速度同期閾値 (m/s²):", self.acceleration_threshold)

        # 終了重力レベル
        self.end_gravity_level = QDoubleSpinBox()
        self.end_gravity_level.setRange(0.1, 10.0)
        self.end_gravity_level.setDecimals(2)
        self.end_gravity_level.setSingleStep(0.1)
        self.end_gravity_level.setValue(self.config["end_gravity_level"])
        form_layout3.addRow("終了重力レベル (G):", self.end_gravity_level)

        # ウィンドウサイズ
        self.window_size = QDoubleSpinBox()
        self.window_size.setRange(0.01, 10.0)
        self.window_size.setDecimals(2)
        self.window_size.setSingleStep(0.01)
        self.window_size.setValue(self.config["window_size"])
        form_layout3.addRow("解析ウィンドウサイズ (秒):", self.window_size)

        # 開始点からの最小秒数
        self.min_seconds_after_start = QDoubleSpinBox()
        self.min_seconds_after_start.setRange(0.0, 10.0)
        self.min_seconds_after_start.setDecimals(2)
        self.min_seconds_after_start.setSingleStep(0.1)
        self.min_seconds_after_start.setValue(self.config.get("min_seconds_after_start", 0.0))
        form_layout3.addRow("終了点の開始点からの最小秒数 (秒):", self.min_seconds_after_start)

        # G-quality解析設定グループ
        g_quality_group = QGroupBox("G-quality解析設定")
        form_layout4 = QFormLayout(g_quality_group)

        # G-quality解析パラメータ
        self._init_g_quality_widgets(form_layout4)

        # 各グループをメインレイアウトに追加
        layout.addWidget(input_group)
        layout.addWidget(perf_group)
        layout.addWidget(display_group)
        layout.addWidget(analysis_group)
        layout.addWidget(g_quality_group)

        # ダイアログボタン
        self._init_buttons(layout)

    def _init_g_quality_widgets(self, form_layout):
        """
        G-quality解析関連のウィジェットを初期化する

        Args:
            form_layout (QFormLayout): 設定項目を追加するフォームレイアウト
        """
        # G-quality開始ウィンドウサイズ
        self.g_quality_start = QDoubleSpinBox()
        self.g_quality_start.setRange(0.01, 10.0)
        self.g_quality_start.setDecimals(2)
        self.g_quality_start.setSingleStep(0.01)
        self.g_quality_start.setValue(self.config["g_quality_start"])
        form_layout.addRow("G-quality解析開始ウィンドウサイズ (秒):", self.g_quality_start)

        # G-quality終了ウィンドウサイズ
        self.g_quality_end = QDoubleSpinBox()
        self.g_quality_end.setRange(0.01, 10.0)
        self.g_quality_end.setDecimals(2)
        self.g_quality_end.setSingleStep(0.01)
        self.g_quality_end.setValue(self.config["g_quality_end"])
        form_layout.addRow("G-quality解析終了ウィンドウサイズ (秒):", self.g_quality_end)

        # G-qualityステップサイズ
        self.g_quality_step = QDoubleSpinBox()
        self.g_quality_step.setRange(0.01, 1.0)
        self.g_quality_step.setDecimals(2)
        self.g_quality_step.setSingleStep(0.01)
        self.g_quality_step.setValue(self.config["g_quality_step"])
        form_layout.addRow("G-quality解析ステップ (秒):", self.g_quality_step)

    def _init_buttons(self, layout):
        """
        ダイアログのボタンを初期化する

        Args:
            layout (QVBoxLayout): ボタンを追加するレイアウト
        """
        # OKとキャンセルボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_settings(self):
        """
        ダイアログからの設定値を辞書として取得する

        Returns:
            dict: 編集された設定データの辞書
        """
        settings = {
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
            "min_seconds_after_start": self.min_seconds_after_start.value(),
            "use_cache": self.use_cache.isChecked(),
            "auto_calculate_g_quality": self.auto_calculate_g_quality.isChecked(),
            "default_graph_duration": self.default_graph_duration.value(),
            "invert_inner_acceleration": self.invert_inner_acceleration.isChecked(),
        }

        logger.debug(f"設定変更: {settings}")
        return settings
