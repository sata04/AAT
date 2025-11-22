#!/usr/bin/env python3
"""
メインウィンドウモジュール

アプリケーションのメインウィンドウとその機能を定義します。
グラフ表示、データテーブル、ファイル処理、解析機能などの
ユーザーインターフェースを提供します。
"""

import os
import sys
from pathlib import Path

# matplotlib バックエンドを明示的に設定（GUI用）
import matplotlib

matplotlib.use("qtagg")  # PySide6対応のバックエンドを使用
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import SpanSelector
from PySide6.QtCore import QMutex, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.cache_manager import delete_cache
from core.config import load_config, save_config
from core.data_processor import detect_columns, filter_data, load_and_process_data
from core.exceptions import ColumnNotFoundError
from core.export import create_output_directories, export_data, export_g_quality_data
from core.logger import get_logger, log_exception
from core.paths import resolve_base_dir
from core.statistics import calculate_statistics
from core.version import APP_VERSION
from gui.column_selector_dialog import ColumnSelectorDialog
from gui.settings_dialog import SettingsDialog
from gui.styles import Colors, ThemeType, apply_theme, get_toggle_checkbox_styles
from gui.widgets import ToggleSwitch
from gui.workers import GQualityWorker

# メインウィンドウ用のロガーを初期化
logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ

    CSVデータの読み込み、処理、表示、解析、およびエクスポート機能を提供します。
    Inner CapsuleとDrag Shieldの重力レベルデータをグラフおよび表形式で
    表示し、G-quality解析などの高度な分析機能も備えています。
    """

    def __init__(self):
        """
        MainWindowクラスのコンストラクタ

        UIの初期化、日本語フォントの設定、およびデータ構造の初期化を行います。
        """
        super().__init__()
        logger.info("メインウィンドウの初期化を開始")

        # Qtメッセージの抑制
        self._suppress_qt_messages()

        # 設定の読み込み（テーマ適用前に必要）
        self.config = load_config(on_warning=self._notify_warning)

        # テーマ状態の初期化（UI構築より前に必要）
        self.current_theme_type = ThemeType.from_config(self.config.get("theme"))

        # テーマの適用
        apply_theme(QApplication.instance(), self.current_theme_type)

        # 日本語フォント設定
        self._setup_japanese_font()

        # ウィンドウの基本設定
        self.setWindowTitle("AAT (Acceleration Analysis Tool)")
        self.resize(1280, 850)

        # UI要素の初期化
        self._setup_ui()
        self._setup_menus()

        # データと状態の初期化
        self._initialize_data()
        self._update_data_dependent_controls()

        logger.info("メインウィンドウの初期化が完了しました")

    # ------------------------------------------------
    # 通知/確認ハンドラー（coreとの橋渡し）
    # ------------------------------------------------

    def _confirm_overwrite(self, path: Path) -> bool:
        reply = QMessageBox.question(
            self,
            "確認",
            f"出力ファイルが既に存在します:\n{path}\n上書きしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _notify_warning(self, message: str) -> None:
        QMessageBox.warning(self, "警告", message)

    def _notify_info(self, message: str) -> None:
        QMessageBox.information(self, "保存完了", message)

    # ------------------------------------------------
    # 初期設定関連メソッド
    # ------------------------------------------------

    def _setup_japanese_font(self):
        """
        プラットフォームに応じた日本語フォントを設定する
        """
        try:
            # macOS向け
            if sys.platform == "darwin":
                font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
                if os.path.exists(font_path):
                    font_prop = font_manager.FontProperties(fname=font_path)
                    plt.rcParams["font.family"] = font_prop.get_name()
            # Windows向け
            elif sys.platform == "win32":
                font_path = "C:\\Windows\\Fonts\\msgothic.ttc"
                if os.path.exists(font_path):
                    font_prop = font_manager.FontProperties(fname=font_path)
                    plt.rcParams["font.family"] = font_prop.get_name()
            # Linux向け
            elif sys.platform.startswith("linux"):
                # 一般的な日本語フォント
                for font_path in [
                    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                ]:
                    if os.path.exists(font_path):
                        font_prop = font_manager.FontProperties(fname=font_path)
                        plt.rcParams["font.family"] = font_prop.get_name()
                        break

            # Matplotlibのデフォルトフォントサイズを調整
            plt.rcParams["font.size"] = 10
            plt.rcParams["axes.titlesize"] = 12
            plt.rcParams["axes.labelsize"] = 10

        except Exception as e:
            log_exception(e, "フォント設定中にエラー")
            # フォント設定に失敗した場合はデフォルトフォントを使用
            plt.rcParams["font.family"] = "sans-serif"
            logger.info("デフォルトフォントにフォールバック: sans-serif")

    def _create_badge(self, text, object_name="Badge"):
        """
        シンプルなバッジラベルを生成する
        """
        badge = QLabel(text)
        badge.setObjectName(object_name)
        badge.setContentsMargins(10, 4, 10, 4)
        return badge

    def _set_badge(self, badge: QLabel, text: str, object_name: str):
        """
        バッジのテキストとスタイルを更新する
        """
        badge.setText(text)
        badge.setObjectName(object_name)
        # Reapply style so the changed object name takes effect immediately
        badge.style().unpolish(badge)
        badge.style().polish(badge)

    def _setup_ui(self):
        """
        UIコンポーネントを初期化する
        """
        from PySide6.QtWidgets import QFrame

        # メインウィジェットとレイアウトの設定
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # --- ヘッダーセクション ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # タイトルとステータス
        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)
        title_label = QLabel("AAT (Acceleration Analysis Tool)")
        title_label.setObjectName("Header")
        self.status_label = QLabel("ファイルを選択してください")
        self.status_label.setObjectName("Status")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.status_label)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)
        self.dataset_badge = self._create_badge("ファイル未選択", "BadgeMuted")
        self.mode_badge = self._create_badge("通常モード", "BadgeInfo")
        self.view_badge = self._create_badge("表示: トリミング", "BadgeMuted")
        self.theme_badge = self._create_badge("テーマ: システム", "BadgeMuted")
        badge_row.addWidget(self.dataset_badge)
        badge_row.addWidget(self.mode_badge)
        badge_row.addWidget(self.view_badge)
        badge_row.addWidget(self.theme_badge)
        badge_row.addStretch()
        title_layout.addLayout(badge_row)

        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        # 処理状況表示
        self.processing_status_label = QLabel("")
        self.processing_status_label.setObjectName("Status")
        self.processing_status_label.setWordWrap(True)
        self.processing_status_label.setVisible(False)
        header_layout.addWidget(self.processing_status_label)

        self.main_layout.addLayout(header_layout)

        # --- コントロールパネル ---
        control_panel = QFrame()
        control_panel.setObjectName("Container")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(15)

        # ファイル操作グループ
        file_group = QHBoxLayout()
        select_button = QPushButton("CSVファイルを選択")
        select_button.clicked.connect(self.select_and_process_file)
        select_button.setCursor(Qt.CursorShape.PointingHandCursor)
        file_group.addWidget(select_button)

        self.compare_button = QPushButton("複数ファイルを比較")
        self.compare_button.setObjectName("Secondary")
        self.compare_button.clicked.connect(self.toggle_comparison)
        self.compare_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.compare_button.setEnabled(False)
        file_group.addWidget(self.compare_button)

        control_layout.addLayout(file_group)

        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"background-color: {Colors.BORDER}; width: 1px;")
        control_layout.addWidget(line)

        # 解析・表示グループ
        analysis_group = QHBoxLayout()

        self.g_quality_mode_button = QPushButton("G-quality評価")
        self.g_quality_mode_button.setObjectName("Secondary")
        self.g_quality_mode_button.setCheckable(True)
        self.g_quality_mode_button.clicked.connect(self.toggle_g_quality_mode)
        self.g_quality_mode_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.g_quality_mode_button.setEnabled(False)
        analysis_group.addWidget(self.g_quality_mode_button)

        self.show_all_button = QPushButton("全体を表示")
        self.show_all_button.setObjectName("Secondary")
        self.show_all_button.setCheckable(True)
        self.show_all_button.clicked.connect(self.toggle_show_all_data)
        self.show_all_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_all_button.setEnabled(False)
        analysis_group.addWidget(self.show_all_button)

        control_layout.addLayout(analysis_group)

        control_layout.addStretch()

        # 設定・ツールグループ
        tools_group = QHBoxLayout()

        self.dataset_selector = QComboBox()
        self.dataset_selector.setMinimumWidth(200)
        self.dataset_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.dataset_selector.setMinimumContentsLength(16)
        self.dataset_selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.dataset_selector.currentIndexChanged.connect(self.update_selected_dataset)
        tools_group.addWidget(self.dataset_selector)

        settings_button = QPushButton("設定")
        settings_button.setObjectName("Secondary")
        settings_button.clicked.connect(self.open_settings)
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        tools_group.addWidget(settings_button)

        clear_cache_button = QPushButton("キャッシュクリア")
        clear_cache_button.setObjectName("Secondary")
        clear_cache_button.clicked.connect(self.clear_cache)
        clear_cache_button.setCursor(Qt.CursorShape.PointingHandCursor)
        tools_group.addWidget(clear_cache_button)

        control_layout.addLayout(tools_group)

        self.main_layout.addWidget(control_panel)

        # --- プログレスバー ---
        self.progress_container = QWidget()
        self.progress_container.setObjectName("Container")
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(12, 12, 12, 12)
        progress_layout.setSpacing(5)

        # ファイル単位の進捗
        file_progress_layout = QHBoxLayout()
        self.file_progress_label = QLabel("ファイル処理:")
        self.file_progress_label.setObjectName("Status")
        self.file_progress_bar = QProgressBar()
        file_progress_layout.addWidget(self.file_progress_label)
        file_progress_layout.addWidget(self.file_progress_bar)
        progress_layout.addLayout(file_progress_layout)

        # 全体の進捗
        total_progress_layout = QHBoxLayout()
        self.progress_label = QLabel("全体進捗:")
        self.progress_label.setObjectName("Status")
        self.progress_bar = QProgressBar()
        total_progress_layout.addWidget(self.progress_label)
        total_progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(total_progress_layout)

        self.progress_container.setVisible(False)
        self.main_layout.addWidget(self.progress_container)

        # --- メインコンテンツ (グラフとテーブル) ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(2)
        self.main_layout.addWidget(splitter)

        # グラフウィジェット
        graph_container = QFrame()
        graph_container.setObjectName("Container")
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(0)

        # Matplotlibのスタイル設定
        self.figure = plt.figure(figsize=(10, 6), facecolor=Colors.BG_SECONDARY)
        self.canvas = FigureCanvas(self.figure)
        self._set_canvas_background()
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: transparent; border: none;")
        # Matplotlibのサブプロット設定ダイアログなどにテーマを適用するためのフック
        self.toolbar.actionTriggered.connect(self._on_toolbar_action_triggered)

        graph_panel = QWidget()
        graph_panel_layout = QVBoxLayout(graph_panel)
        graph_panel_layout.setContentsMargins(0, 0, 0, 0)
        graph_panel_layout.setSpacing(6)
        graph_panel_layout.addWidget(self.toolbar)
        graph_panel_layout.addWidget(self.canvas)

        self.empty_state = QWidget()
        empty_state_layout = QVBoxLayout(self.empty_state)
        empty_state_layout.setContentsMargins(24, 32, 24, 32)
        empty_state_layout.setSpacing(10)
        empty_state_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_title = QLabel("まだデータがありません")
        self.empty_title.setObjectName("EmptyStateTitle")
        self.empty_text = QLabel(
            "CSVファイルを読み込んでグラフと統計を表示してください。\n複数ファイルもまとめて追加できます。"
        )
        self.empty_text.setObjectName("Status")
        self.empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_text.setWordWrap(True)
        empty_button = QPushButton("CSVファイルを選択")
        empty_button.clicked.connect(self.select_and_process_file)
        empty_state_layout.addWidget(self.empty_title, alignment=Qt.AlignmentFlag.AlignHCenter)
        empty_state_layout.addWidget(self.empty_text)
        empty_state_layout.addWidget(empty_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.graph_stack = QStackedLayout()
        self.graph_stack.setContentsMargins(0, 0, 0, 0)
        self.graph_stack.addWidget(self.empty_state)
        self.graph_stack.addWidget(graph_panel)
        self.graph_stack.setCurrentWidget(self.empty_state)

        graph_layout.addLayout(self.graph_stack)
        splitter.addWidget(graph_container)

        # データテーブル
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        splitter.addWidget(self.table)

        # スプリッターの初期サイズ比率設定 (グラフ:テーブル = 2:1)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        # 範囲選択機能の変数を初期化
        self.span_selectors = []

    def _setup_menus(self):
        """メニューバーを設定する"""
        menubar = self.menuBar()
        if menubar is None:
            return

        if sys.platform == "darwin":
            menubar.setNativeMenuBar(True)

        file_menu = menubar.addMenu("ファイル")
        if file_menu is not None:
            self.open_file_action = QAction("CSVファイルを開く...", self)
            self.open_file_action.setShortcut(QKeySequence.StandardKey.Open)
            self.open_file_action.triggered.connect(self.select_and_process_file)
            file_menu.addAction(self.open_file_action)

            file_menu.addSeparator()

            self.exit_action = QAction("終了", self)
            self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
            self.exit_action.triggered.connect(self.close)
            file_menu.addAction(self.exit_action)

        view_menu = menubar.addMenu("表示")
        if view_menu is not None:
            # Theme Submenu
            theme_menu = view_menu.addMenu("テーマ")

            self.theme_action_group = QActionGroup(self)

            self.system_theme_action = QAction("システムデフォルト", self)
            self.system_theme_action.setCheckable(True)
            self.system_theme_action.setChecked(True)  # Default to System
            self.system_theme_action.triggered.connect(lambda: self._change_theme(ThemeType.SYSTEM))
            self.theme_action_group.addAction(self.system_theme_action)
            theme_menu.addAction(self.system_theme_action)

            self.dark_theme_action = QAction("ダークモード", self)
            self.dark_theme_action.setCheckable(True)
            self.dark_theme_action.triggered.connect(lambda: self._change_theme(ThemeType.DARK))
            self.theme_action_group.addAction(self.dark_theme_action)
            theme_menu.addAction(self.dark_theme_action)

            self.light_theme_action = QAction("ライトモード", self)
            self.light_theme_action.setCheckable(True)
            self.light_theme_action.triggered.connect(lambda: self._change_theme(ThemeType.LIGHT))
            self.theme_action_group.addAction(self.light_theme_action)
            theme_menu.addAction(self.light_theme_action)

            view_menu.addSeparator()

            self.compare_action = QAction("比較モード", self)
            self.compare_action.setCheckable(True)
            self.compare_action.triggered.connect(self._handle_compare_action)
            view_menu.addAction(self.compare_action)

            self.show_all_action = QAction("全体を表示", self)
            self.show_all_action.setCheckable(True)
            self.show_all_action.triggered.connect(self._handle_show_all_action)
            view_menu.addAction(self.show_all_action)

        analysis_menu = menubar.addMenu("解析")
        if analysis_menu is not None:
            self.g_quality_action = QAction("G-quality評価モード", self)
            self.g_quality_action.setCheckable(True)
            self.g_quality_action.triggered.connect(self._handle_g_quality_action)
            analysis_menu.addAction(self.g_quality_action)

        tools_menu = menubar.addMenu("ツール")
        if tools_menu is not None:
            self.settings_action = QAction("設定...", self)
            self.settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
            self.settings_action.triggered.connect(self.open_settings)
            tools_menu.addAction(self.settings_action)

            self.clear_cache_action = QAction("キャッシュをクリア", self)
            self.clear_cache_action.triggered.connect(self.clear_cache)
            tools_menu.addAction(self.clear_cache_action)

        help_menu = menubar.addMenu("ヘルプ")
        if help_menu is None:
            return

        about_action = QAction("AAT について", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _handle_compare_action(self, checked):
        """メニューの比較モード切替を処理する"""
        if checked != self.is_comparing:
            self.toggle_comparison()
        self._sync_menu_state()

    def _handle_show_all_action(self, checked):
        """メニューの全体表示切替を処理する"""
        if self.is_g_quality_mode or not self.show_all_button.isEnabled():
            self._sync_menu_state()
            return

        if self.show_all_button.isChecked() != checked:
            self.show_all_button.setChecked(checked)
        self.toggle_show_all_data()
        self._sync_menu_state()

    def _handle_g_quality_action(self, checked):
        """メニューのG-qualityモード切替を処理する"""
        if self.g_quality_mode_button.isEnabled():
            if self.g_quality_mode_button.isChecked() != checked:
                self.g_quality_mode_button.setChecked(checked)
            self.toggle_g_quality_mode()
        self._sync_menu_state()

    def _sync_menu_state(self):
        """ボタンとメニューの状態を同期する"""
        dataset_count = len(getattr(self, "processed_data", {}))

        if hasattr(self, "compare_action"):
            blocked = self.compare_action.blockSignals(True)
            self.compare_action.setChecked(self.is_comparing)
            self.compare_action.blockSignals(blocked)
            self.compare_action.setText(self.compare_button.text())
            self.compare_action.setEnabled(dataset_count >= 2 or self.is_comparing)

        if hasattr(self, "show_all_action"):
            blocked = self.show_all_action.blockSignals(True)
            self.show_all_action.setChecked(self.is_showing_all_data)
            self.show_all_action.blockSignals(blocked)
            self.show_all_action.setText(self.show_all_button.text())
            self.show_all_action.setEnabled(
                self.show_all_button.isEnabled() and self.show_all_button.isVisible() and not self.is_g_quality_mode
            )

        if hasattr(self, "g_quality_action"):
            blocked = self.g_quality_action.blockSignals(True)
            self.g_quality_action.setChecked(self.is_g_quality_mode)
            self.g_quality_action.blockSignals(blocked)
            self.g_quality_action.setText(self.g_quality_mode_button.text())
            self.g_quality_action.setEnabled(self.g_quality_mode_button.isEnabled())

    def _sync_theme_menu_state(self):
        """テーマメニューのチェック状態を現在のテーマに合わせる"""
        actions = {
            ThemeType.SYSTEM: getattr(self, "system_theme_action", None),
            ThemeType.DARK: getattr(self, "dark_theme_action", None),
            ThemeType.LIGHT: getattr(self, "light_theme_action", None),
        }
        actions = {theme_type: action for theme_type, action in actions.items() if action is not None}
        if not actions:
            return

        target_action = actions.get(self.current_theme_type, actions.get(ThemeType.SYSTEM))
        for action in actions.values():
            blocked = action.blockSignals(True)
            action.setChecked(action is target_action)
            action.blockSignals(blocked)

    def _update_data_dependent_controls(self):
        """データ有無に応じて操作可能なコントロールを更新する"""
        dataset_count = len(getattr(self, "processed_data", {}))
        has_data = dataset_count > 0

        if not has_data:
            # データがない場合はモード状態をリセット
            self.is_comparing = False
            self.compare_button.setText("複数ファイルを比較")
            self.is_g_quality_mode = False
            self.g_quality_mode_button.setChecked(False)
            self.is_showing_all_data = False
            self.show_all_button.setChecked(False)

        self.g_quality_mode_button.setEnabled(has_data)
        self.show_all_button.setEnabled(has_data)
        self.compare_button.setEnabled(has_data and (dataset_count >= 2 or self.is_comparing))

        self._sync_menu_state()
        self._refresh_badges()

    def _show_graph_panel(self):
        """空状態からグラフパネルに切り替える"""
        if hasattr(self, "graph_stack"):
            self.graph_stack.setCurrentIndex(1)

    def _show_empty_state(self, message=None):
        """データ未読込時の空状態を表示する"""
        if message and hasattr(self, "empty_text"):
            self.empty_text.setText(message)
        if hasattr(self, "graph_stack"):
            self.graph_stack.setCurrentIndex(0)

    def _refresh_badges(self):
        """ヘッダーのバッジ表示を最新の状態に更新する"""
        dataset_count = len(getattr(self, "processed_data", {}))
        dataset_text = f"{dataset_count} ファイル" if dataset_count else "ファイル未選択"
        dataset_style = "BadgeAccent" if dataset_count else "BadgeMuted"
        self._set_badge(self.dataset_badge, dataset_text, dataset_style)

        if self.is_g_quality_mode:
            mode_text = "モード: G-quality"
            mode_style = "BadgeAccent"
        elif self.is_comparing:
            mode_text = "モード: 比較"
            mode_style = "BadgeInfo"
        else:
            mode_text = "モード: 通常"
            mode_style = "BadgeInfo"
        self._set_badge(self.mode_badge, mode_text, mode_style)

        view_text = "表示: 全体" if self.is_showing_all_data else "表示: トリミング"
        view_style = "BadgeInfo" if self.is_showing_all_data else "BadgeMuted"
        self._set_badge(self.view_badge, view_text, view_style)

        theme_map = {
            ThemeType.DARK: "テーマ: ダーク",
            ThemeType.LIGHT: "テーマ: ライト",
            ThemeType.SYSTEM: "テーマ: システム",
        }
        theme_text = theme_map.get(self.current_theme_type, "テーマ: システム")
        self._set_badge(self.theme_badge, theme_text, "BadgeMuted")

    def _resolve_sensor_visibility(self, inner_series, drag_series) -> tuple[bool, bool]:
        """
        設定とデータ有無に基づき、グラフに表示するセンサーを決定する
        """
        mode = self.config.get("graph_sensor_mode", "both")
        has_inner = inner_series is not None and not inner_series.empty
        has_drag = drag_series is not None and not drag_series.empty

        show_inner = has_inner and mode in ("both", "inner_only")
        show_drag = has_drag and mode in ("both", "drag_only")

        # 希望したセンサーが欠落している場合は、利用可能なデータをフォールバック表示
        if mode == "inner_only" and not show_inner and has_drag:
            show_drag = True
        if mode == "drag_only" and not show_drag and has_inner:
            show_inner = True
        if not show_inner and not show_drag:
            show_inner = has_inner
            show_drag = has_drag

        return show_inner, show_drag

    def _show_about_dialog(self):
        """バージョン情報ダイアログを表示する"""
        message = (
            f"<b>Acceleration Analysis Tool (AAT)</b><br>"
            f"バージョン: {APP_VERSION}<br>"
            "微小重力環境下での実験データ分析を支援する PySide6 アプリケーションです。"
        )
        QMessageBox.about(self, "AAT について", message)

    def _initialize_data(self):
        """
        データと状態変数を初期化する
        """
        # データ保存用辞書
        self.processed_data = {}

        # 設定の読み込み
        if not hasattr(self, "config"):
            self.config = load_config(on_warning=self._notify_warning)

        # 各種フラグの初期化
        self.is_comparing = False
        self.is_g_quality_mode = False
        self.is_showing_all_data = False
        self.g_quality_data = None
        self.is_g_quality_analysis_running = False

        # Current Theme State
        self.current_theme_type = ThemeType.from_config(self.config.get("theme"))

        # System theme listener
        try:
            QApplication.instance().styleHints().colorSchemeChanged.connect(self._handle_system_theme_change)
        except Exception as e:
            logger.warning(f"システムテーマ変更の監視設定に失敗しました: {e}")

        # ワーカースレッド配列の初期化
        self.workers = []

        # ワーカー操作用のミューテックス
        self.worker_mutex = QMutex()

        # ファイル名とパスのマッピング
        self.file_paths = {}  # ファイル名とパスを保存する辞書

        self._sync_theme_menu_state()
        self._refresh_badges()

    def _clear_span_selectors(self):
        """
        SpanSelectorを安全にクリアする
        """
        try:
            for span in self.span_selectors:
                if hasattr(span, "disconnect"):
                    span.disconnect()
                # matplotlibオブジェクトの明示的な削除
                if hasattr(span, "ax"):
                    span.ax = None
            self.span_selectors.clear()
            logger.debug("SpanSelectorを安全にクリアしました")
        except Exception as e:
            logger.warning(f"SpanSelectorのクリア中にエラー: {e}")
            # エラーが発生してもリストはクリア
            self.span_selectors.clear()

    def _add_version_watermark(self, ax, color=None):
        """
        グラフ右下にアプリのバージョンを表示する（直書き禁止）
        """
        try:
            ax.text(
                0.98,
                0.02,
                f"AAT v{APP_VERSION}",
                transform=ax.transAxes,
                fontsize=8,
                verticalalignment="bottom",
                horizontalalignment="right",
                color=color or Colors.TEXT_SECONDARY,
            )
        except Exception as e:
            logger.debug(f"バージョンウォーターマークの追加に失敗: {e}")

    def _matplotlib_palette(self):
        """Qtパレットから現在の背景/テキスト色を取得し、Matplotlib用に返す"""
        # Qtパレットに依存するとライトでも暗くなるケースがあるため、テーマ種別で決め打ちする
        if self.current_theme_type == ThemeType.LIGHT:
            return (
                Colors.LIGHT_BG_PRIMARY,
                Colors.LIGHT_BG_SECONDARY,
                Colors.LIGHT_TEXT_PRIMARY,
                Colors.LIGHT_TEXT_SECONDARY,
                Colors.LIGHT_BORDER,
            )

        # DARK/SYSTEM は Colors の現在値を使用
        return Colors.BG_PRIMARY, Colors.BG_SECONDARY, Colors.TEXT_PRIMARY, Colors.TEXT_SECONDARY, Colors.BORDER

    def _set_canvas_background(self):
        """キャンバスとFigureの背景色をQtパレットに合わせる"""
        bg_primary, bg_secondary, _, _, _ = self._matplotlib_palette()
        if hasattr(self, "figure"):
            self.figure.patch.set_facecolor(bg_secondary)
        if hasattr(self, "canvas"):
            self.canvas.setStyleSheet(f"background-color: {bg_primary};")

    def _apply_axes_theme(self, ax, secondary_ax=None, legends=None):
        """
        Matplotlib Axesに現在のテーマカラーを適用する
        """
        try:
            bg_primary, bg_secondary, text_primary, text_secondary, border = self._matplotlib_palette()

            ax.set_facecolor(bg_secondary)
            for spine in ax.spines.values():
                spine.set_color(border)
            ax.tick_params(colors=text_secondary, which="both")
            ax.xaxis.label.set_color(text_primary)
            ax.yaxis.label.set_color(text_primary)
            ax.title.set_color(text_primary)
            ax.grid(True, linestyle="--", alpha=0.3, color=text_secondary)

            if secondary_ax is not None:
                for spine in secondary_ax.spines.values():
                    spine.set_color(border)
                secondary_ax.tick_params(colors=text_secondary, which="both")
                secondary_ax.xaxis.label.set_color(text_primary)
                secondary_ax.yaxis.label.set_color(text_primary)

            if legends:
                for legend in legends:
                    if legend:
                        legend.set_facecolor(bg_secondary)
                        frame = legend.get_frame()
                        frame.set_edgecolor(border)
                        for text in legend.get_texts():
                            text.set_color(text_primary)
        except Exception as e:
            logger.debug(f"テーマ適用中にエラー: {e}")

    def _suppress_qt_messages(self):
        """
        特定のQtメッセージを抑制し、macOS固有の設定を最適化する
        """
        try:
            from PySide6.QtCore import QtMsgType, qInstallMessageHandler
            from PySide6.QtWidgets import QApplication

            def message_handler(msg_type, context, message):
                # macOS固有の抑制対象メッセージ
                suppressed_messages = [
                    "Layer-backing is always enabled",
                    "Window move completed without beginning",
                    "TSM",
                    "kCGErrorIllegalArgument",
                    "ApplePersistenceIgnoreState",
                    "QCocoaWindow",
                    "Qt internal warning",
                ]

                # 抑制対象メッセージをチェック
                if any(suppressed in message for suppressed in suppressed_messages):
                    return

                # 重要なエラーは必ず出力
                if msg_type == QtMsgType.QtCriticalMsg:
                    logger.error(f"Qt Critical: {message}")
                elif msg_type == QtMsgType.QtFatalMsg:
                    logger.critical(f"Qt Fatal: {message}")
                    # 致命的なエラーの場合は詳細情報も出力
                    if context:
                        logger.critical(
                            f"Context - File: {context.file}, Line: {context.line}, Function: {context.function}"
                        )
                elif msg_type == QtMsgType.QtWarningMsg:
                    # 重要でない警告は抑制、重要な警告は出力
                    if any(keyword in message.lower() for keyword in ["crash", "abort", "segmentation", "exception"]):
                        logger.warning(f"Qt Warning: {message}")

            # カスタムメッセージハンドラを設定
            qInstallMessageHandler(message_handler)

            # macOS固有の追加設定
            if sys.platform == "darwin":
                app = QApplication.instance()
                if app:
                    # アプリケーション属性の設定（PySide6で利用可能なもののみ）
                    try:
                        # PySide6ではAA_EnableHighDpiScalingとAA_UseHighDpiPixmapsは削除されました
                        # High DPIサポートはデフォルトで有効になっています
                        if hasattr(Qt.ApplicationAttribute, "AA_DontShowIconsInMenus"):
                            app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True)

                        # macOS固有のスタイル設定
                        if hasattr(Qt.ApplicationAttribute, "AA_DontUseNativeMenuBar"):
                            app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)
                    except Exception as attr_error:
                        logger.warning(f"一部のQt属性設定に失敗しました: {attr_error}")

            logger.info("QtメッセージハンドラとmacOS設定を最適化しました")

        except Exception as e:
            log_exception(e, "Qtメッセージハンドラの設定に失敗")
            logger.warning("デフォルトのQt設定を使用します")

    def _handle_system_theme_change(self, scheme):
        """システムテーマの変更を検知して適用する"""
        if self.current_theme_type == ThemeType.SYSTEM:
            logger.info(f"システムテーマの変更を検知しました: {scheme}")
            # Re-apply SYSTEM theme to trigger detection logic
            self._change_theme(ThemeType.SYSTEM)

    def _change_theme(self, theme_type: ThemeType):
        """
        アプリケーションのテーマを変更する

        Args:
            theme_type (ThemeType): 適用するテーマタイプ
        """
        try:
            logger.info(f"テーマを変更します: {theme_type.name}")
            self.current_theme_type = theme_type

            apply_theme(QApplication.instance(), theme_type)
            theme_preference = theme_type.to_config_value()
            if self.config.get("theme") != theme_preference:
                self.config["theme"] = theme_preference
                save_config(self.config, on_error=self._notify_warning)

            self._sync_theme_menu_state()

            # Update matplotlib figure background if needed
            if hasattr(self, "figure"):
                self._set_canvas_background()
                # Apply theme to all existing axes
                for ax in self.figure.axes:
                    self._apply_axes_theme(ax, legends=[ax.get_legend()])
                self.canvas.draw()

            # Update status
            self.status_label.setText(f"テーマを {theme_type.name} に変更しました")
            self._refresh_badges()

        except Exception as e:
            log_exception(e, "テーマ変更中にエラーが発生しました")
            QMessageBox.warning(self, "エラー", f"テーマの変更に失敗しました: {e}")

    # ------------------------------------------------
    # ファイル処理関連メソッド
    # ------------------------------------------------

    def select_and_process_file(self):
        """
        CSVファイルを選択し、データを処理する

        ファイル選択ダイアログを表示し、選択されたCSVファイルを
        読み込んで処理します。CSVファイル内の列が判断できない場合は
        列選択ダイアログを表示します。キャッシュが有効な場合は
        キャッシュからデータを読み込みます。
        """
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "CSVファイルを選択", "", "CSV files (*.csv)")
            if not file_paths:
                logger.info("ファイルは選択されませんでした")
                return

            total_files = len(file_paths)
            logger.info(f"選択されたファイル数: {total_files}")
            self.status_label.setText("処理中...")

            # 進捗表示の初期化
            self.progress_container.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(total_files)

            # ファイル進捗表示の初期化
            self.file_progress_bar.setValue(0)
            self.file_progress_bar.setMaximum(100)

            # 処理状況表示の初期化
            self.processing_status_label.setVisible(True)
            self.processing_status_label.setText("処理を開始します...")

            QApplication.processEvents()

            # キャッシュモジュールをインポート
            from core.cache_manager import (
                generate_cache_id,
                has_valid_cache,
                load_from_cache,
                save_to_cache,
            )

            for file_idx, file_path in enumerate(file_paths):
                logger.info(f"ファイル処理開始 ({file_idx + 1}/{total_files}): {file_path}")
                file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]
                existing_path = self.file_paths.get(file_name_without_ext)
                force_reprocess = False
                force_g_quality = False
                temp_config = None

                # 進捗更新
                self.progress_bar.setValue(file_idx)
                self.processing_status_label.setText(f"処理中: {file_name_without_ext} ({file_idx + 1}/{total_files})")
                QApplication.processEvents()

                # 既に処理済みのファイルを選択した場合の対応
                if file_name_without_ext in self.processed_data:
                    same_file = False
                    if existing_path:
                        try:
                            same_file = os.path.samefile(existing_path, file_path)
                        except Exception:
                            same_file = os.path.abspath(existing_path) == os.path.abspath(file_path)

                    dialog = QMessageBox(self)
                    dialog.setIcon(QMessageBox.Icon.Question)
                    dialog.setWindowTitle("再処理の確認")

                    if same_file:
                        dialog.setText(
                            f"{file_name_without_ext} はこのセッションですでに処理済みです。\n"
                            "保存済みの結果を再利用しますか？"
                        )
                        reuse_button = dialog.addButton("再利用", QMessageBox.ButtonRole.YesRole)
                        rerun_button = dialog.addButton("再処理して上書き", QMessageBox.ButtonRole.AcceptRole)
                        skip_button = dialog.addButton("スキップ", QMessageBox.ButtonRole.RejectRole)
                        dialog.setDefaultButton(reuse_button)
                    else:
                        dialog.setText(
                            f"{file_name_without_ext} は既に別のファイルで処理済みです。\n"
                            f"既存: {existing_path or '不明'}\n"
                            f"新規: {file_path}\n"
                            "どのように処理しますか？"
                        )
                        reuse_button = dialog.addButton("既存の結果を維持", QMessageBox.ButtonRole.YesRole)
                        rerun_button = dialog.addButton("新しいファイルで処理", QMessageBox.ButtonRole.AcceptRole)
                        skip_button = dialog.addButton("スキップ", QMessageBox.ButtonRole.RejectRole)
                        dialog.setDefaultButton(rerun_button)

                    dialog.exec()
                    clicked_button = dialog.clickedButton()

                    if clicked_button == reuse_button:
                        self.processing_status_label.setText(
                            f"処理済みデータを再利用: {file_name_without_ext} ({file_idx + 1}/{total_files})"
                        )
                        self.progress_bar.setValue(file_idx + 1)
                        self.file_progress_bar.setValue(100)
                        QApplication.processEvents()
                        continue

                    if clicked_button == skip_button:
                        self.processing_status_label.setText(f"スキップ: {file_name_without_ext}")
                        self.progress_bar.setValue(file_idx + 1)
                        QApplication.processEvents()
                        continue

                    # 再処理を選択した場合はキャッシュを使わず最後まで再実行
                    force_reprocess = True
                    force_g_quality = True
                    # 既存の処理結果をクリアして整合性を保つ
                    self.processed_data.pop(file_name_without_ext, None)
                    self.file_paths.pop(file_name_without_ext, None)
                    try:
                        from core.cache_manager import delete_cache

                        delete_cache(file_path)
                    except Exception as cache_error:
                        logger.debug(f"キャッシュ削除に失敗しましたが処理を継続します: {cache_error}")
                    self.processing_status_label.setText(
                        f"再処理中: {file_name_without_ext} ({file_idx + 1}/{total_files})"
                    )

                # キャッシュの確認
                if self.config.get("use_cache", True) and not force_reprocess:
                    has_cache, cache_id = has_valid_cache(file_path, self.config)
                    if has_cache:
                        # キャッシュの再利用について確認
                        reply = QMessageBox.question(
                            self,
                            "キャッシュ検出",
                            f"このファイル({file_name_without_ext})の処理済みデータが見つかりました。\n再利用しますか？",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        )

                        if reply == QMessageBox.StandardButton.Yes:
                            # キャッシュからデータを読み込む
                            self.processing_status_label.setText(
                                f"キャッシュからデータを読み込み中... ({file_idx + 1}/{total_files})"
                            )
                            QApplication.processEvents()

                            cached_data = load_from_cache(file_path, cache_id)
                            if cached_data:
                                # キャッシュデータをロード
                                self.processed_data[file_name_without_ext] = cached_data
                                self.file_paths[file_name_without_ext] = file_path
                                logger.info(f"キャッシュからデータをロードしました: {file_name_without_ext}")

                                # ファイル進捗を100%に設定
                                self.file_progress_bar.setValue(100)

                                # 自動G-quality評価がオンで、キャッシュにG-quality評価がない場合は計算
                                if (
                                    self.config.get("auto_calculate_g_quality", True)
                                    and "g_quality_data" not in cached_data
                                ):
                                    self.processing_status_label.setText(
                                        f"G-quality評価を計算中... ({file_idx + 1}/{total_files})"
                                    )
                                    QApplication.processEvents()

                                    # G-quality評価を計算
                                    self.calculate_g_quality_for_dataset(file_name_without_ext, file_idx, total_files)

                                # 次のファイルへ
                                continue

                # 通常の処理フロー（キャッシュがない場合またはキャッシュを使用しない場合）
                self.processing_status_label.setText(f"データを読み込み中... ({file_idx + 1}/{total_files})")
                QApplication.processEvents()

                # データの読み込みと処理
                try:
                    # 元のCSVデータを読み込む
                    raw_data = pd.read_csv(file_path)
                    self.file_progress_bar.setValue(20)
                    QApplication.processEvents()

                    # データの読み込みを試みる
                    (
                        time,
                        gravity_level_inner_capsule,
                        gravity_level_drag_shield,
                        adjusted_time,
                    ) = load_and_process_data(file_path, self.config)
                    self.file_progress_bar.setValue(40)
                    QApplication.processEvents()

                except ColumnNotFoundError:
                    # 時間列と加速度列の候補を取得
                    time_columns, accel_columns = detect_columns(file_path)

                    if not time_columns:
                        QMessageBox.critical(
                            self,
                            "エラー",
                            "CSVファイルに時間列の候補が見つかりませんでした。",
                        )
                        continue

                    if not accel_columns:
                        QMessageBox.critical(
                            self,
                            "エラー",
                            "CSVファイルに加速度列の候補が見つかりませんでした。",
                        )
                        continue

                    # 列選択ダイアログを表示（片側のみの利用にも対応）
                    dialog = ColumnSelectorDialog(time_columns, accel_columns, self)
                    if dialog.exec():
                        # ダイアログから選択された列を取得
                        time_column, inner_column, drag_column, use_inner, use_drag = dialog.get_selected_columns()

                        # 一時的に設定を上書き
                        temp_config = self.config.copy()
                        temp_config.update(
                            {
                                "time_column": time_column,
                                "acceleration_column_inner_capsule": inner_column,
                                "acceleration_column_drag_shield": drag_column,
                                "use_inner_acceleration": use_inner,
                                "use_drag_acceleration": use_drag,
                            }
                        )

                        # 再度データの読み込みを試みる
                        try:
                            raw_data = pd.read_csv(file_path)
                            self.file_progress_bar.setValue(20)
                            QApplication.processEvents()

                            (
                                time,
                                gravity_level_inner_capsule,
                                gravity_level_drag_shield,
                                adjusted_time,
                            ) = load_and_process_data(file_path, temp_config)
                            self.file_progress_bar.setValue(40)
                            QApplication.processEvents()

                            # 列選択が成功した場合、ユーザーに設定を保存するか尋ねる
                            reply = QMessageBox.question(
                                self,
                                "設定の保存",
                                "選択した列設定をデフォルトとして保存しますか？",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            )

                            if reply == QMessageBox.StandardButton.Yes:
                                self.config.update(temp_config)
                                save_config(self.config, on_error=self._notify_warning)
                                logger.info("列設定を保存しました")
                            else:
                                logger.info("列設定は一時的に使用されますが、保存はしません")
                        except Exception as e2:
                            log_exception(e2, "選択された列でのデータ読み込み中にエラーが発生")
                            QMessageBox.critical(
                                self,
                                "エラー",
                                f"選択された列でのデータ読み込みに失敗しました: {str(e2)}",
                            )
                            continue
                    else:
                        # ダイアログがキャンセルされた場合は次のファイルへ
                        logger.info("列選択がキャンセルされました")
                        continue

                # データのフィルタリング
                self.processing_status_label.setText(f"データをフィルタリング中... ({file_idx + 1}/{total_files})")
                QApplication.processEvents()

                (
                    filtered_time,
                    filtered_gravity_level_inner_capsule,
                    filtered_gravity_level_drag_shield,
                    filtered_adjusted_time,
                    end_index,
                ) = filter_data(
                    time,
                    gravity_level_inner_capsule,
                    gravity_level_drag_shield,
                    adjusted_time,
                    self.config,
                )
                self.file_progress_bar.setValue(60)
                QApplication.processEvents()

                # 処理結果を保存
                self.processed_data[file_name_without_ext] = {
                    "time": time,
                    "adjusted_time": adjusted_time,
                    "gravity_level_inner_capsule": gravity_level_inner_capsule,
                    "gravity_level_drag_shield": gravity_level_drag_shield,
                    "filtered_time": filtered_time,
                    "filtered_adjusted_time": filtered_adjusted_time,
                    "filtered_gravity_level_inner_capsule": filtered_gravity_level_inner_capsule,
                    "filtered_gravity_level_drag_shield": filtered_gravity_level_drag_shield,
                    "end_index": end_index,
                    "raw_data": raw_data,  # 元のCSVデータを保存
                    "use_inner_acceleration": (temp_config or self.config).get("use_inner_acceleration", True),
                    "use_drag_acceleration": (temp_config or self.config).get("use_drag_acceleration", True),
                    "has_inner_data": not filtered_gravity_level_inner_capsule.empty,
                    "has_drag_data": not filtered_gravity_level_drag_shield.empty,
                }
                self.file_paths[file_name_without_ext] = file_path
                logger.info(f"データ処理完了: {file_name_without_ext}")

                # データをキャッシュに保存
                if self.config.get("use_cache", True):
                    self.processing_status_label.setText(
                        f"データをキャッシュに保存中... ({file_idx + 1}/{total_files})"
                    )
                    QApplication.processEvents()

                    cache_id = generate_cache_id(file_path, self.config)
                    save_to_cache(
                        self.processed_data[file_name_without_ext],
                        file_path,
                        cache_id,
                        self.config,
                    )

                # グラフの作成と保存
                self.processing_status_label.setText(f"グラフを作成中... ({file_idx + 1}/{total_files})")
                QApplication.processEvents()

                graph_path = self.plot_gravity_level(
                    filtered_time,
                    filtered_adjusted_time,
                    filtered_gravity_level_inner_capsule,
                    filtered_gravity_level_drag_shield,
                    self.config,
                    file_name_without_ext,
                    file_path,
                )
                logger.info(f"グラフを保存: {graph_path}")
                self.file_progress_bar.setValue(70)
                QApplication.processEvents()

                # 統計情報の計算と保存
                self.processing_status_label.setText(f"統計情報を計算中... ({file_idx + 1}/{total_files})")
                QApplication.processEvents()

                (
                    min_mean_inner_capsule,
                    min_time_inner_capsule,
                    min_std_inner_capsule,
                ) = calculate_statistics(filtered_gravity_level_inner_capsule, filtered_time, self.config)
                min_mean_drag_shield, min_time_drag_shield, min_std_drag_shield = calculate_statistics(
                    filtered_gravity_level_drag_shield,
                    filtered_adjusted_time,
                    self.config,
                )
                self.file_progress_bar.setValue(80)
                QApplication.processEvents()

                # データエクスポート用の設定を準備
                # 列選択ダイアログで選択した場合は、その選択情報を使用する
                export_config = self.config.copy()
                if temp_config is not None:
                    # 列選択ダイアログで選択した列情報を優先的に使用
                    export_config.update(
                        {
                            "time_column": temp_config["time_column"],
                            "acceleration_column_inner_capsule": temp_config["acceleration_column_inner_capsule"],
                            "acceleration_column_drag_shield": temp_config["acceleration_column_drag_shield"],
                        }
                    )
                    logger.info(
                        f"選択された列情報を使用してExcelエクスポート: "
                        f"時間列={temp_config['time_column']}, "
                        f"内カプセル加速度列={temp_config['acceleration_column_inner_capsule']}, "
                        f"外カプセル加速度列={temp_config['acceleration_column_drag_shield']}"
                    )

                # データのエクスポート
                self.processing_status_label.setText(f"データをエクスポート中... ({file_idx + 1}/{total_files})")
                QApplication.processEvents()

                export_data(
                    filtered_time,
                    filtered_adjusted_time,
                    filtered_gravity_level_inner_capsule,
                    filtered_gravity_level_drag_shield,
                    file_path,
                    min_mean_inner_capsule,
                    min_time_inner_capsule,
                    min_std_inner_capsule,
                    min_mean_drag_shield,
                    min_time_drag_shield,
                    min_std_drag_shield,
                    graph_path,
                    filtered_time,  # フィルタリング済みの時間データを追加
                    filtered_adjusted_time,  # フィルタリング済みの調整時間データを追加
                    export_config,  # 最新の設定情報を渡す
                    raw_data,  # 元のCSVデータを渡す
                    confirm_overwrite=self._confirm_overwrite,
                    notify_warning=self._notify_warning,
                    notify_info=self._notify_info,
                )
                logger.info(f"データエクスポート完了: {file_name_without_ext}")
                self.file_progress_bar.setValue(90)
                QApplication.processEvents()

                # 自動G-quality評価がオンの場合は計算
                if self.config.get("auto_calculate_g_quality", True):
                    self.calculate_g_quality_for_dataset(
                        file_name_without_ext, file_idx, total_files, force=force_g_quality
                    )

                # ファイル処理完了
                self.file_progress_bar.setValue(100)
                QApplication.processEvents()

            # 全体進捗を完了に設定
            self.progress_bar.setValue(total_files)

            # UI更新
            self.update_table()
            self.update_dataset_selector()  # このメソッドが更新され、明示的にupdate_selected_datasetを呼び出すようになります
            self.status_label.setText("処理が完了しました")
            self.processing_status_label.setText("すべてのファイルの処理が完了しました")
            logger.info("すべてのファイルの処理が完了しました")

            # 必要に応じてキャンバスを強制的に更新
            self.canvas.draw_idle()

            # 3秒後にプログレスバーを非表示にする
            QTimer.singleShot(3000, lambda: self.progress_container.setVisible(False))

        except Exception as e:
            log_exception(e, "ファイル処理中に例外が発生")
            self.status_label.setText("エラーが発生しました")
            self.processing_status_label.setText(f"エラー: {str(e)}")
            QMessageBox.critical(self, "エラー", str(e))
        finally:
            self._update_data_dependent_controls()

    def calculate_g_quality_for_dataset(self, dataset_name, file_idx, total_files, force=False):
        """
        指定されたデータセットに対してG-quality評価を行う

        Args:
            dataset_name (str): データセット名
            file_idx (int): ファイルインデックス
            total_files (int): 総ファイル数
            force (bool): 既存結果があっても再計算するかどうか
        """
        if dataset_name not in self.processed_data:
            logger.warning(f"データセットが見つかりません: {dataset_name}")
            return

        data = self.processed_data[dataset_name]
        original_file_path = self.file_paths.get(dataset_name)

        # G-quality評価が既に存在するかチェック
        if "g_quality_data" in data and not force:
            logger.info(f"G-quality評価は既に存在します: {dataset_name}")
            return
        if force:
            data.pop("g_quality_data", None)

        self.processing_status_label.setText(f"G-quality評価を計算中... ({file_idx + 1}/{total_files})")
        QApplication.processEvents()

        # G-qualityワーカーを作成して実行
        worker = GQualityWorker(
            data["filtered_time"],
            data["filtered_gravity_level_inner_capsule"],
            data["filtered_gravity_level_drag_shield"],
            self.config,
            file_idx,
            total_files,
            data["filtered_adjusted_time"],
        )

        # 同期的に実行する（非同期実行の複雑さを避けるため）
        g_quality_data = []

        # 進捗状況更新のためのコールバック
        def update_file_progress(value):
            self.file_progress_bar.setValue(value)
            QApplication.processEvents()

        def update_status(status):
            self.processing_status_label.setText(status)
            QApplication.processEvents()

        # シグナルを接続
        worker.progress.connect(update_file_progress)
        worker.status_update.connect(update_status)

        # ワーカーを実行
        worker.run()
        g_quality_data = worker.get_results()

        # 結果を保存
        self.processed_data[dataset_name]["g_quality_data"] = g_quality_data

        # G-qualityグラフを描画
        graph_path = self.plot_g_quality_data(g_quality_data, dataset_name)

        # 結果をファイルに保存（グラフパスも渡す）
        if original_file_path:
            export_g_quality_data(g_quality_data, original_file_path, graph_path)
        # キャッシュに保存
        if self.config.get("use_cache", True) and original_file_path:
            from core.cache_manager import generate_cache_id, save_to_cache

            cache_id = generate_cache_id(original_file_path, self.config)
            save_to_cache(
                self.processed_data[dataset_name],
                original_file_path,
                cache_id,
                self.config,
            )

        logger.info(f"G-quality評価が完了しました: {dataset_name}")

    def hide_progress_bars(self):
        """
        すべてのプログレスバーとステータスラベルを非表示にする
        """
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.file_progress_bar.setVisible(False)
        self.file_progress_label.setVisible(False)
        self.processing_status_label.setVisible(False)

    # ------------------------------------------------
    # UI更新関連メソッド
    # ------------------------------------------------

    def update_dataset_selector(self):
        """
        データセットセレクターのコンボボックスを更新する
        """
        # シグナルを一時的にブロック
        self.dataset_selector.blockSignals(True)

        self.dataset_selector.clear()

        if self.is_comparing:
            self.dataset_selector.addItem("複数グラフ比較")
        else:
            dataset_names = list(self.processed_data.keys())
            if dataset_names:
                self.dataset_selector.addItems(dataset_names)
            else:
                # データセットがない場合はプレースホルダーを表示
                self.dataset_selector.addItem("データがありません")
                self._show_empty_state("CSVファイルを読み込んでグラフを表示します。")

        # シグナルのブロックを解除
        self.dataset_selector.blockSignals(False)

        # データセットが存在する場合に最初のアイテムを選択
        if self.dataset_selector.count() > 0:
            self.dataset_selector.setCurrentIndex(0)
            # 明示的にデータセットの更新メソッドを呼び出す
            self.update_selected_dataset()
        self._sync_menu_state()
        self._refresh_badges()

    def update_selected_dataset(self):
        """
        選択されたデータセットに応じてグラフを更新する
        """
        try:
            if not self.processed_data:
                self._show_empty_state("CSVファイルを読み込んでグラフを表示します。")
                return

            if self.is_comparing:
                self.plot_comparison()
            else:
                selected_dataset = self.dataset_selector.currentText()

                # 「データがありません」のプレースホルダーの場合は何もしない
                if selected_dataset == "データがありません":
                    self._show_empty_state("CSVファイルを読み込んでグラフを表示します。")
                    return

                if selected_dataset in self.processed_data:
                    data = self.processed_data[selected_dataset]
                    if self.is_g_quality_mode and "g_quality_data" in data:
                        self.plot_g_quality_data(data["g_quality_data"], selected_dataset)
                    elif self.is_showing_all_data:
                        self.show_all_data(data)
                    else:
                        # 正しいファイルパスを取得
                        original_file_path = self.file_paths.get(selected_dataset, "")
                        self.plot_gravity_level(
                            data["filtered_time"],
                            data["filtered_adjusted_time"],
                            data["filtered_gravity_level_inner_capsule"],
                            data["filtered_gravity_level_drag_shield"],
                            self.config,
                            selected_dataset,
                            original_file_path,
                        )
                else:
                    logger.debug(f"選択されたデータセットが見つかりません: {selected_dataset}")
                    # ユーザーにはエラーを表示しない
                    self._show_empty_state("選択されたデータが見つかりません。")

            # グラフの描画を強制的に更新
            self.canvas.draw_idle()
        except Exception as e:
            log_exception(e, "グラフ更新中にエラーが発生")
            logger.error(f"グラフ更新エラー: {str(e)}")

    def update_button_visibility(self):
        """
        現在のモードに応じてボタンの表示状態を更新する
        """
        self.compare_button.setVisible(True)
        self.g_quality_mode_button.setVisible(True)
        self.show_all_button.setVisible(not self.is_g_quality_mode)

    def update_table(self):
        """
        データテーブルを現在のモードに応じて更新する
        """
        if self.is_g_quality_mode:
            self.update_g_quality_table()
        else:
            self.update_standard_table()

    def update_standard_table(self):
        """
        標準モードでのデータテーブルを更新する
        """
        self.table.setRowCount(len(self.processed_data))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "File Name",
                "Inner Capsule: Start Time of Min SD Window for Given Window Size (s)",
                "Inner Capsule: Mean G-Level in Min SD Window (G)",
                "Inner Capsule: SD in Min SD Window (G)",
                "Drag Shield: Start Time of Min SD Window for Given Window Size (s)",
                "Drag Shield: Mean G-Level in Min SD Window (G)",
                "Drag Shield: SD in Min SD Window (G)",
            ]
        )

        for row, (file_name, data) in enumerate(self.processed_data.items()):
            # 各ファイルの統計情報を計算
            min_mean_inner_capsule, min_time_inner_capsule, min_std_inner_capsule = calculate_statistics(
                data["filtered_gravity_level_inner_capsule"],
                data["filtered_time"],
                self.config,
            )
            min_mean_drag_shield, min_time_drag_shield, min_std_drag_shield = calculate_statistics(
                data["filtered_gravity_level_drag_shield"],
                data["filtered_adjusted_time"],
                self.config,
            )

            # テーブルにデータを設定（Noneチェックを追加）
            self.table.setItem(row, 0, QTableWidgetItem(file_name))
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(f"{min_time_inner_capsule:.3f}" if min_time_inner_capsule is not None else "None"),
            )
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(f"{min_mean_inner_capsule:.4f}" if min_mean_inner_capsule is not None else "None"),
            )
            self.table.setItem(
                row,
                3,
                QTableWidgetItem(f"{min_std_inner_capsule:.4f}" if min_std_inner_capsule is not None else "None"),
            )
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(f"{min_time_drag_shield:.3f}" if min_time_drag_shield is not None else "None"),
            )
            self.table.setItem(
                row,
                5,
                QTableWidgetItem(f"{min_mean_drag_shield:.4f}" if min_mean_drag_shield is not None else "None"),
            )
            self.table.setItem(
                row,
                6,
                QTableWidgetItem(f"{min_std_drag_shield:.4f}" if min_std_drag_shield is not None else "None"),
            )

        self.table.resizeColumnsToContents()

    def update_g_quality_table(self):
        """
        G-qualityモードでのデータテーブルを更新する
        """
        all_g_quality_data = []
        for dataset_name, data in self.processed_data.items():
            if "g_quality_data" in data:
                for row in data["g_quality_data"]:
                    all_g_quality_data.append([dataset_name] + list(row))

        self.table.setRowCount(len(all_g_quality_data))
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Dataset",
                "Analysis Window Size (s)",
                "Inner Capsule: Start Time of Min SD Window for Given Window Size (s)",
                "Inner Capsule: Mean G-Level in Min SD Window (G)",
                "Inner Capsule: SD in Min SD Window (G)",
                "Drag Shield: Start Time of Min SD Window for Given Window Size (s)",
                "Drag Shield: Mean G-Level in Min SD Window (G)",
                "Drag Shield: SD in Min SD Window (G)",
            ]
        )

        for row, (
            dataset,
            window_size,
            min_time_inner_capsule,
            min_mean_inner_capsule,
            min_std_inner_capsule,
            min_time_drag_shield,
            min_mean_drag_shield,
            min_std_drag_shield,
        ) in enumerate(all_g_quality_data):
            self.table.setItem(row, 0, QTableWidgetItem(dataset))
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(f"{window_size:.3f}" if window_size is not None else "None"),
            )
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(f"{min_time_inner_capsule:.3f}" if min_time_inner_capsule is not None else "None"),
            )
            self.table.setItem(
                row,
                3,
                QTableWidgetItem(f"{min_mean_inner_capsule:.4f}" if min_mean_inner_capsule is not None else "None"),
            )
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(f"{min_std_inner_capsule:.4f}" if min_std_inner_capsule is not None else "None"),
            )
            self.table.setItem(
                row,
                5,
                QTableWidgetItem(f"{min_time_drag_shield:.3f}" if min_time_drag_shield is not None else "None"),
            )
            self.table.setItem(
                row,
                6,
                QTableWidgetItem(f"{min_mean_drag_shield:.4f}" if min_mean_drag_shield is not None else "None"),
            )
            self.table.setItem(
                row,
                7,
                QTableWidgetItem(f"{min_std_drag_shield:.4f}" if min_std_drag_shield is not None else "None"),
            )

        self.table.resizeColumnsToContents()

    # ------------------------------------------------
    # グラフ表示関連メソッド
    # ------------------------------------------------

    def plot_gravity_level(
        self,
        time,
        adjusted_time,
        gravity_level_inner_capsule,
        gravity_level_drag_shield,
        config,
        file_name_without_ext,
        original_file_path,
    ):
        """
        重力レベルのグラフを描画し、必要に応じて保存する

        Args:
            time (pandas.Series): 時間データ
            adjusted_time (pandas.Series): 調整された時間データ
            gravity_level_inner_capsule (pandas.Series): Inner Capsuleの重力レベル
            gravity_level_drag_shield (pandas.Series): Drag Shieldの重力レベル
            config (dict): 設定情報
            file_name_without_ext (str): ファイル名（拡張子なし）
            original_file_path (str): 元のファイルパス

        Returns:
            str or None: 保存されたグラフのパス。保存されない場合はNone。
        """

        self._show_graph_panel()
        self.figure.clear()
        self.figure.patch.set_facecolor(Colors.BG_SECONDARY)

        ax = self.figure.add_subplot(111)
        show_inner, show_drag = self._resolve_sensor_visibility(gravity_level_inner_capsule, gravity_level_drag_shield)

        if not show_inner and not show_drag:
            ax.text(
                0.5,
                0.5,
                "表示できる加速度データがありません",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
                fontsize=14,
            )
            self.canvas.draw()
            return None

        # Inner Capsuleは元の時間で、Drag Shieldは調整後の時間でプロット
        if show_inner:
            ax.plot(
                time,
                gravity_level_inner_capsule,
                label=f"{file_name_without_ext} (Inner Capsule)",
                linewidth=0.8,
            )
        if show_drag:
            ax.plot(
                adjusted_time,
                gravity_level_drag_shield,
                label=f"{file_name_without_ext} (Drag Shield)",
                linewidth=0.8,
            )

        ax.set_ylim(config["ylim_min"], config["ylim_max"])

        # x軸の範囲を設定（デフォルト1.45秒で固定、グラフサイズを統一）
        default_duration = config.get("default_graph_duration", 1.45)
        ax.set_xlim(0, default_duration)

        ax.set_title(f"The Gravity Level {file_name_without_ext}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Gravity Level (G)")
        ax.grid(True, alpha=0.3)
        ax.legend()

        # テーマ色を適用
        self._apply_axes_theme(ax, legends=[ax.get_legend()])

        # グラフの右下にバージョンを表示
        self._add_version_watermark(ax)

        # 範囲選択機能を追加
        # 既存のSpanSelectorを安全にクリア
        self._clear_span_selectors()

        # SpanSelectorを追加
        span = SpanSelector(
            ax,
            self.on_select_range,
            "horizontal",
            useblit=True,
            props={"alpha": 0.3, "facecolor": "tab:blue"},
            interactive=True,
            drag_from_anywhere=True,
        )
        self.span_selectors.append(span)

        self.canvas.draw()

        # グラフの保存: CSVファイルのディレクトリを基準に保存先を作成
        if not original_file_path:
            logger.warning("original_file_pathが空です。グラフを保存できません。")
            return None

        try:
            # エクスポート用の設定を取得
            export_width = config.get("export_figure_width", 10)
            export_height = config.get("export_figure_height", 6)
            export_dpi = config.get("export_dpi", 300)
            export_bbox = config.get("export_bbox_inches", None)
            bbox_inches = "tight" if export_bbox == "tight" else None

            # エクスポート用のfigureを作成
            export_fig = plt.figure(figsize=(export_width, export_height))
            export_ax = export_fig.add_subplot(111)

            # グラフを再描画（エクスポート用）
            if show_inner:
                export_ax.plot(
                    time,
                    gravity_level_inner_capsule,
                    label=f"{file_name_without_ext} (Inner Capsule)",
                    linewidth=0.8,
                )
            if show_drag:
                export_ax.plot(
                    adjusted_time,
                    gravity_level_drag_shield,
                    label=f"{file_name_without_ext} (Drag Shield)",
                    linewidth=0.8,
                )

            export_ax.set_ylim(config["ylim_min"], config["ylim_max"])
            export_ax.set_xlim(0, config.get("default_graph_duration", 1.45))
            export_ax.set_title(f"The Gravity Level {file_name_without_ext}")
            export_ax.set_xlabel("Time (s)")
            export_ax.set_ylabel("Gravity Level (G)")
            export_ax.grid(True, alpha=0.3)
            export_ax.legend()

            # グラフの右下にバージョンを表示
            self._add_version_watermark(export_ax)

            export_fig.tight_layout()

            # グラフを保存
            csv_dir = os.path.dirname(original_file_path)
            logger.debug(f"CSV directory: {csv_dir}")
            logger.debug(f"Original file path: {original_file_path}")
            results_dir, graphs_dir = create_output_directories(csv_dir)
            logger.debug(f"Results directory: {results_dir}")
            logger.debug(f"Graphs directory: {graphs_dir}")
            graph_path = os.path.join(graphs_dir, f"{file_name_without_ext}_gl.png")
            export_fig.savefig(graph_path, dpi=export_dpi, bbox_inches=bbox_inches)
            logger.info(
                f"グラフを保存しました: {graph_path} (サイズ: {export_width}x{export_height}, DPI: {export_dpi})"
            )

            # エクスポート用figureをクローズ
            plt.close(export_fig)

            return graph_path

        except Exception as e:
            logger.error(f"グラフの保存中にエラーが発生しました: {e}")
            return None

    def plot_comparison(self):
        """
        複数のデータセットを比較するグラフを描画する
        """
        logger.info("比較グラフのプロット開始")
        self._show_graph_panel()
        self.figure.clear()
        self.figure.patch.set_facecolor(Colors.BG_SECONDARY)
        ax = self.figure.add_subplot(111)

        # カラーマップを使用して、各データセットに異なる色を割り当てる
        colors = plt.get_cmap("rainbow")(np.linspace(0, 1, len(self.processed_data) * 2))
        color_index = 0
        plotted_any = False

        for file_name, data in self.processed_data.items():
            if self.is_g_quality_mode:
                g_quality_rows = data.get("g_quality_data") or []
                if g_quality_rows:
                    inner_points = [(row[0], row[2]) for row in g_quality_rows if row[2] is not None]
                    drag_points = [(row[0], row[5]) for row in g_quality_rows if row[5] is not None]

                    if inner_points:
                        ax.plot(
                            [p[0] for p in inner_points],
                            [p[1] for p in inner_points],
                            label=f"{file_name} (Inner Capsule)",
                            color=colors[color_index],
                        )
                        color_index += 1
                        plotted_any = True

                    if drag_points:
                        ax.plot(
                            [p[0] for p in drag_points],
                            [p[1] for p in drag_points],
                            label=f"{file_name} (Drag Shield)",
                            color=colors[color_index],
                        )
                        color_index += 1
                        plotted_any = True

                    if not inner_points and not drag_points:
                        logger.info(f"G-quality比較: {file_name} にプロット可能なデータがありません")
            else:
                if self.is_showing_all_data:
                    inner_series = data["gravity_level_inner_capsule"]
                    drag_series = data["gravity_level_drag_shield"]
                    inner_time = data["time"]
                    drag_time = data["adjusted_time"]
                else:
                    inner_series = data["filtered_gravity_level_inner_capsule"]
                    drag_series = data["filtered_gravity_level_drag_shield"]
                    inner_time = data["filtered_time"]
                    drag_time = data["filtered_adjusted_time"]

                show_inner, show_drag = self._resolve_sensor_visibility(inner_series, drag_series)

                if show_inner:
                    ax.plot(
                        inner_time,
                        inner_series,
                        label=f"{file_name} (Inner Capsule)",
                        linewidth=0.8,
                        color=colors[color_index],
                    )
                    color_index += 1
                    plotted_any = True
                if show_drag:
                    ax.plot(
                        drag_time,
                        drag_series,
                        label=f"{file_name} (Drag Shield)",
                        linewidth=0.8,
                        color=colors[color_index],
                    )
                    color_index += 1
                    plotted_any = True

        # グラフのタイトルと軸ラベルの設定
        if self.is_g_quality_mode:
            ax.set_title("G-quality Analysis Comparison")
            ax.set_xlabel("Window Size (s)")
            ax.set_ylabel("Mean Gravity Level (G)")
        else:
            ax.set_title("Gravity Level Comparison")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Gravity Level (G)")
            if not self.is_showing_all_data:
                ax.set_ylim(self.config["ylim_min"], self.config["ylim_max"])
                # 比較モードでもX軸の範囲を統一（デフォルト1.45秒で固定）
                default_duration = self.config.get("default_graph_duration", 1.45)
                ax.set_xlim(0, default_duration)

        if not plotted_any:
            ax.text(
                0.5,
                0.5,
                "比較できるデータがありません",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
                fontsize=14,
            )

        legend = ax.legend() if plotted_any else None
        # テーマ色を適用
        self._apply_axes_theme(ax, legends=[legend])

        # グラフの右下にバージョンを表示
        self._add_version_watermark(ax)

        # 比較モードではSpanSelectorを追加しない（選択範囲の統計計算を無効化）
        self._clear_span_selectors()

        self.canvas.draw()

    def plot_g_quality_data(self, g_quality_data, file_name):
        """
        G-quality解析データをグラフ表示する

        Args:
            g_quality_data (list): G-quality解析結果のリスト
            file_name (str): ファイル名
        """
        self._show_graph_panel()
        # original_file_pathをファイルパス辞書から取得
        original_file_path = self.file_paths.get(file_name)

        self.figure.clear()
        self.figure.patch.set_facecolor(Colors.BG_SECONDARY)
        ax = self.figure.add_subplot(111)

        # G-qualityデータが空でないことを確認
        if not g_quality_data:
            ax.text(
                0.5,
                0.5,
                "G-qualityデータが不十分です\nデータ長を確認してください",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
                fontsize=14,
            )
            ax.set_title(f"G-quality Analysis: {file_name}")
            self.canvas.draw()
            return None

        inner_points = [(row[0], row[2]) for row in g_quality_data if row[2] is not None]
        drag_points = [(row[0], row[5]) for row in g_quality_data if row[5] is not None]

        if inner_points:
            ax.plot(
                [p[0] for p in inner_points],
                [p[1] for p in inner_points],
                color="darkblue",
                label="Inner Capsule: Mean Gravity Level",
            )
        if drag_points:
            ax.plot(
                [p[0] for p in drag_points],
                [p[1] for p in drag_points],
                color="red",
                label="Drag Shield: Mean Gravity Level",
            )
        ax.set_xlabel("Window Size (s)")
        ax.set_ylabel("Mean Gravity Level (G)")

        ax2 = ax.twinx()
        inner_std_points = [(row[0], row[3]) for row in g_quality_data if row[3] is not None]
        drag_std_points = [(row[0], row[6]) for row in g_quality_data if row[6] is not None]

        if inner_std_points:
            ax2.plot(
                [p[0] for p in inner_std_points],
                [p[1] for p in inner_std_points],
                color="dodgerblue",
                label="Inner Capsule: Standard Deviation",
            )
        if drag_std_points:
            ax2.plot(
                [p[0] for p in drag_std_points],
                [p[1] for p in drag_std_points],
                color="violet",
                label="Drag Shield: Standard Deviation",
            )
        ax2.set_ylabel("Standard Deviation (G)")

        ax.set_title(f"G-quality Analysis - {file_name}")
        legends = []
        if ax.get_legend_handles_labels()[0]:
            legends.append(ax.legend(loc="upper left"))
        if ax2.get_legend_handles_labels()[0]:
            legends.append(ax2.legend(loc="upper right"))

        # テーマ色を適用（GUI表示のみ）
        self._apply_axes_theme(ax, secondary_ax=ax2, legends=legends)

        self.figure.tight_layout()

        # グラフの右下にバージョンを表示
        self._add_version_watermark(ax)

        # SpanSelectorをクリア（G-qualityモードでは選択範囲機能を無効化）
        self._clear_span_selectors()

        # グラフ保存パスを設定 (ファイル名_gq.png形式)
        # 型チェック: original_file_pathが文字列でなければ終了
        if not isinstance(original_file_path, str) or not original_file_path:
            logger.warning("G-quality: original_file_pathが無効です。グラフを保存できません。")
            self.canvas.draw()
            return None

        # エクスポート用の設定を取得
        export_width = self.config.get("export_figure_width", 10)
        export_height = self.config.get("export_figure_height", 6)
        export_dpi = self.config.get("export_dpi", 300)
        export_bbox = self.config.get("export_bbox_inches", None)
        bbox_inches = "tight" if export_bbox == "tight" else None

        # エクスポート用のfigureを作成
        export_fig = plt.figure(figsize=(export_width, export_height))
        export_ax = export_fig.add_subplot(111)

        # グラフを再描画（エクスポート用）
        export_inner_points = [(row[0], row[2]) for row in g_quality_data if row[2] is not None]
        export_drag_points = [(row[0], row[5]) for row in g_quality_data if row[5] is not None]

        if export_inner_points:
            export_ax.plot(
                [p[0] for p in export_inner_points],
                [p[1] for p in export_inner_points],
                color="darkblue",
                label="Inner Capsule: Mean Gravity Level",
            )
        if export_drag_points:
            export_ax.plot(
                [p[0] for p in export_drag_points],
                [p[1] for p in export_drag_points],
                color="red",
                label="Drag Shield: Mean Gravity Level",
            )
        export_ax.set_xlabel("Window Size (s)")
        export_ax.set_ylabel("Mean Gravity Level (G)")

        export_ax2 = export_ax.twinx()
        export_inner_std_points = [(row[0], row[3]) for row in g_quality_data if row[3] is not None]
        export_drag_std_points = [(row[0], row[6]) for row in g_quality_data if row[6] is not None]

        if export_inner_std_points:
            export_ax2.plot(
                [p[0] for p in export_inner_std_points],
                [p[1] for p in export_inner_std_points],
                color="dodgerblue",
                label="Inner Capsule: Standard Deviation",
            )
        if export_drag_std_points:
            export_ax2.plot(
                [p[0] for p in export_drag_std_points],
                [p[1] for p in export_drag_std_points],
                color="violet",
                label="Drag Shield: Standard Deviation",
            )
        export_ax2.set_ylabel("Standard Deviation (G)")

        export_ax.set_title(f"G-quality Analysis - {file_name}")
        export_ax.grid(True)
        export_ax.legend(loc="upper left")
        export_ax2.legend(loc="upper right")

        # グラフの右下にバージョンを表示
        self._add_version_watermark(export_ax)

        export_fig.tight_layout()

        # 出力ディレクトリ構造を作成（export.pyと同じロジック）

        csv_dir = os.path.dirname(original_file_path)
        logger.debug(f"G-quality: CSV directory: {csv_dir}")
        logger.debug(f"G-quality: Original file path: {original_file_path}")
        results_dir, graphs_dir = create_output_directories(csv_dir)
        logger.debug(f"G-quality: Results directory: {results_dir}")
        logger.debug(f"G-quality: Graphs directory: {graphs_dir}")
        graph_path = os.path.join(graphs_dir, f"{file_name}_gq.png")
        export_fig.savefig(graph_path, dpi=export_dpi, bbox_inches=bbox_inches)
        logger.info(
            f"G-qualityグラフを保存しました: {graph_path} (サイズ: {export_width}x{export_height}, DPI: {export_dpi})"
        )

        # エクスポート用figureをクローズ
        plt.close(export_fig)

        self.canvas.draw()
        return graph_path

    def show_all_data(self, data):
        """
        フィルタリング前のすべてのデータをグラフ表示する

        Args:
            data (dict): 表示するデータ
        """
        self._show_graph_panel()
        self.figure.clear()
        self.figure.patch.set_facecolor(Colors.BG_SECONDARY)
        ax = self.figure.add_subplot(111)

        show_inner, show_drag = self._resolve_sensor_visibility(
            data.get("gravity_level_inner_capsule"), data.get("gravity_level_drag_shield")
        )

        if not show_inner and not show_drag:
            ax.text(
                0.5,
                0.5,
                "表示できる加速度データがありません",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
                fontsize=14,
            )
            self.canvas.draw()
            return

        # 全データを表示（マイナスの時間も含む）
        if show_inner:
            ax.plot(
                data["time"],
                data["gravity_level_inner_capsule"],
                color="blue",
                linewidth=0.8,
                label="Inner Capsule",
            )
        if show_drag:
            ax.plot(
                data["adjusted_time"],
                data["gravity_level_drag_shield"],
                color="red",
                linewidth=0.8,
                label="Drag Shield",
            )

        # トリミング範囲を強調表示
        # Inner Capsuleの範囲
        if show_inner and not data["filtered_time"].empty:
            ax.axvspan(
                0,
                data["filtered_time"].iloc[-1],
                alpha=0.1,
                color="blue",
                label="Inner Capsule Range",
            )
        # Drag Shieldの範囲
        if show_drag and not data["filtered_adjusted_time"].empty:
            ax.axvspan(
                0,
                data["filtered_adjusted_time"].iloc[-1],
                alpha=0.1,
                color="red",
                label="Drag Shield Range",
            )

        ax.set_title(f"The Gravity Level {self.dataset_selector.currentText()} (All Data)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Gravity Level (G)")
        ax.grid(True, alpha=0.3)

        # 全体表示モードではX軸の制限を設けず、データの全範囲を表示
        # （エクスポート対象の通常グラフのみ1.45秒に固定）

        ax.legend()
        # テーマ色を適用
        self._apply_axes_theme(ax, legends=[ax.get_legend()])

        # グラフの右下にバージョンを表示
        self._add_version_watermark(ax)

        # 全体表示モードではSpanSelectorを追加しない（選択範囲の統計計算を無効化）
        self._clear_span_selectors()

        self.canvas.draw()

    # ------------------------------------------------
    # モード切替関連メソッド
    # ------------------------------------------------

    def toggle_comparison(self):
        """
        比較モードと個別表示モードを切り替える
        """
        if self.is_comparing:
            logger.info("比較モードから個別モードに切り替えます")
            self.return_to_individual()
        else:
            logger.info("個別モードから比較モードに切り替えます")
            self.start_comparison()
        self._refresh_badges()

    def start_comparison(self):
        """
        比較モードを開始する
        """
        if len(self.processed_data) < 2:
            logger.warning("比較モードには少なくとも2つのデータセットが必要です")
            QMessageBox.warning(self, "警告", "比較するには少なくとも2つのファイルが必要です。")
            self._sync_menu_state()
            return

        self.is_comparing = True
        self.compare_button.setText("個別グラフに戻る")
        self.update_dataset_selector()
        self.update_button_visibility()
        self.plot_comparison()
        self._sync_menu_state()
        self._refresh_badges()
        logger.info("比較モードを開始しました")

    def return_to_individual(self):
        """
        個別グラフ表示モードに戻る
        """
        self.is_comparing = False
        self.compare_button.setText("複数ファイルを比較")
        self.update_dataset_selector()
        if self.dataset_selector.count() > 0:
            self.dataset_selector.setCurrentIndex(0)
            self.update_selected_dataset()
        self.update_button_visibility()
        self._sync_menu_state()
        self._refresh_badges()

    def toggle_show_all_data(self):
        """
        全データ表示モードとフィルタリングデータ表示モードを切り替える
        """
        self.is_showing_all_data = self.show_all_button.isChecked()
        if self.is_showing_all_data:
            self.show_all_button.setText("トリミング範囲を表示")
        else:
            self.show_all_button.setText("全体を表示")

        if self.is_comparing:
            self.plot_comparison()
        else:
            self.update_selected_dataset()
        self._sync_menu_state()
        self._refresh_badges()

    def toggle_g_quality_mode(self):
        """
        G-quality評価モードと通常モードを切り替える
        """
        self.is_g_quality_mode = self.g_quality_mode_button.isChecked()

        if self.is_g_quality_mode:
            # G-quality評価モードに切り替え
            if all("g_quality_data" in data for data in self.processed_data.values()):
                # すべてのデータセットですでにG-quality評価が完了している場合
                self.g_quality_mode_button.setText("通常モードに戻る")
                self.update_table()
                self.update_selected_dataset()
                logger.info("すべてのデータセットのG-quality評価データを表示します")
            else:
                # まだG-quality評価が行われていないデータセットがある場合
                self.g_quality_mode_button.setText("G-quality評価モード実行中")
                self.g_quality_mode_button.setEnabled(False)
                missing_data_sets = [name for name, data in self.processed_data.items() if "g_quality_data" not in data]
                logger.info(f"G-quality評価が必要なデータセット: {missing_data_sets}")

                # 確認ダイアログの表示
                if missing_data_sets:
                    reply = QMessageBox.question(
                        self,
                        "G-quality評価",
                        f"一部のデータセット({', '.join(missing_data_sets)})にG-quality評価データがありません。\n計算を実行しますか？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        # 必要なデータセットのG-quality評価を実行
                        total_missing = len(missing_data_sets)

                        # 進捗表示の初期化
                        self.progress_label.setText("G-quality評価の進捗:")
                        self.progress_label.setVisible(True)
                        self.progress_bar.setVisible(True)
                        self.progress_bar.setValue(0)
                        self.progress_bar.setMaximum(total_missing)

                        # ファイル進捗表示の初期化
                        self.file_progress_label.setText("現在のファイル処理進捗:")
                        self.file_progress_label.setVisible(True)
                        self.file_progress_bar.setVisible(True)
                        self.file_progress_bar.setValue(0)

                        # 処理状況表示の初期化
                        self.processing_status_label.setVisible(True)
                        self.processing_status_label.setText("G-quality評価を開始します...")

                        QApplication.processEvents()

                        # G-quality評価を順次実行
                        for idx, dataset_name in enumerate(missing_data_sets):
                            self.progress_bar.setValue(idx)
                            self.calculate_g_quality_for_dataset(dataset_name, idx, total_missing)

                        self.progress_bar.setValue(total_missing)
                        self.processing_status_label.setText("G-quality評価が完了しました")

                        # 3秒後にプログレスバーを非表示にする
                        QTimer.singleShot(3000, self.hide_progress_bars)

                        # 処理完了後の表示更新
                        self.g_quality_mode_button.setText("通常モードに戻る")
                        self.g_quality_mode_button.setEnabled(True)
                        self.update_table()
                        self.update_selected_dataset()
                    else:
                        # 評価せずにモードを切り替え
                        self.g_quality_mode_button.setText("通常モードに戻る")
                        self.g_quality_mode_button.setEnabled(True)
                        self.update_table()
                        self.update_selected_dataset()
                        logger.info("G-quality評価をスキップし、既存のデータのみで表示します")
        else:
            # 通常モードに戻る
            self.g_quality_mode_button.setText("G-quality評価モード")
            self.update_table()
            self.update_selected_dataset()
            logger.info("通常モードに戻ります")

        self.update_button_visibility()
        if self.is_comparing:
            self.plot_comparison()
        self._sync_menu_state()
        self._refresh_badges()

    # ------------------------------------------------
    # G-quality解析関連メソッド
    # ------------------------------------------------

    def perform_g_quality_analysis(
        self,
        filtered_time,
        filtered_gravity_level_inner_capsule,
        filtered_gravity_level_drag_shield,
        file_name,
        original_file_path,
        filtered_adjusted_time=None,
    ):
        """
        指定されたデータに対してG-quality解析を実行する

        Args:
            filtered_time (pandas.Series): フィルタリングされた時間データ
            filtered_gravity_level_inner_capsule (pandas.Series): Inner Capsuleの重力レベル
            filtered_gravity_level_drag_shield (pandas.Series): Drag Shieldの重力レベル
            file_name (str): ファイル名
            original_file_path (str): 元のファイルパス
            filtered_adjusted_time (pandas.Series, optional): Drag Shield用のフィルタリングされた調整時間データ
        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # ワーカースレッドの作成と開始
        worker = GQualityWorker(
            filtered_time,
            filtered_gravity_level_inner_capsule,
            filtered_gravity_level_drag_shield,
            self.config,
            filtered_adjusted_time=filtered_adjusted_time if filtered_adjusted_time is not None else filtered_time,
        )
        self.workers.append(worker)
        worker.progress.connect(self.update_progress)
        worker.finished.connect(
            lambda result: self.on_g_quality_analysis_finished(result, file_name, original_file_path)
        )
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda: self.remove_worker(worker))
        worker.start()

    def perform_g_quality_analysis_for_all_datasets(self):
        """
        すべてのデータセットに対してG-quality解析を実行する
        """
        self.show_progress_bar()  # プログレスバーを表示

        for dataset_name, data in self.processed_data.items():
            original_file_path = self.file_paths.get(dataset_name)
            self.perform_g_quality_analysis(
                data["filtered_time"],
                data["filtered_gravity_level_inner_capsule"],
                data["filtered_gravity_level_drag_shield"],
                dataset_name,
                original_file_path,
                data.get("filtered_adjusted_time"),
            )

    def on_g_quality_analysis_finished(self, g_quality_data, file_name, original_file_path):
        """
        G-quality解析が完了した時の処理
        """
        self.progress_bar.setVisible(False)
        self.is_g_quality_analysis_running = False

        # 結果を保存
        if file_name not in self.processed_data:
            self.processed_data[file_name] = {}
        self.processed_data[file_name]["g_quality_data"] = g_quality_data

        # file_pathsにファイル名とパスを確実に登録
        if original_file_path and file_name not in self.file_paths:
            self.file_paths[file_name] = original_file_path
            logger.info(f"ファイルパスを登録: {file_name} -> {original_file_path}")

        # グラフを描画
        graph_path = self.plot_g_quality_data(g_quality_data, file_name)

        # 結果をExcelファイルに出力（グラフパスも渡す）
        if original_file_path:
            export_path = export_g_quality_data(g_quality_data, original_file_path, graph_path)
            if export_path:
                QMessageBox.information(
                    self,
                    "保存完了",
                    f"G-quality解析の結果が {export_path} に追加されました",
                )

        # この行を削除する（重複呼び出し）
        # self.plot_g_quality_data(g_quality_data, file_name)

        # テーブルを更新
        self.update_g_quality_table()

        # すべてのデータセットの処理が完了したらボタンを有効化
        if all("g_quality_data" in data for data in self.processed_data.values()):
            self.g_quality_mode_button.setEnabled(True)
            self.g_quality_mode_button.setText("通常モードに戻る")

        self.update_table()
        self.update_button_visibility()

    # ------------------------------------------------
    # プログレスバー関連メソッド
    # ------------------------------------------------

    def update_progress(self, value):
        """
        プログレスバーの値を更新する

        Args:
            value (int): 進捗値（0-100）
        """
        self.progress_bar.setValue(value)
        if value >= 100:
            self.progress_bar.setVisible(False)
        else:
            self.progress_bar.setVisible(True)
        QApplication.processEvents()  # UIの更新を確実に行う

    def show_progress_bar(self):
        """
        プログレスバーを表示し、初期化する
        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

    def hide_progress_bar(self):
        """
        プログレスバーを非表示にする
        """
        self.progress_bar.setVisible(False)
        QApplication.processEvents()

    def remove_worker(self, worker):
        """
        完了したワーカーをワーカーリストから削除する

        Args:
            worker (QThread): 削除するワーカーオブジェクト
        """
        if worker in self.workers:
            self.workers.remove(worker)
            logger.debug(f"ワーカーをリストから削除しました。残りのワーカー数: {len(self.workers)}")

    # ------------------------------------------------
    # その他のメソッド
    # ------------------------------------------------

    def open_settings(self):
        """
        設定ダイアログを開く
        """
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            new_settings = dialog.get_settings()
            self.config.update(new_settings)
            save_config(self.config, on_error=self._notify_warning)
            QMessageBox.information(self, "設定保存", "設定が保存されました。")

    def clear_cache(self):
        """
        キャッシュをクリアする
        """
        # 開いているファイルがない場合は案内のみ表示
        if not getattr(self, "file_paths", {}):
            QMessageBox.information(
                self,
                "キャッシュクリア",
                "現在開いているファイルがないため、キャッシュの保存先を特定できません。\nCSVを読み込んだ後に実行してください。",
            )
            return

        # 全ての処理済みデータのキャッシュディレクトリを探す
        cache_targets: list[tuple[Path, Path]] = []
        cache_dirs_found: set[Path] = set()

        # 現在開いているファイルからキャッシュディレクトリを特定
        for file_path in self.file_paths.values():
            path_obj = Path(file_path)
            base_dir = resolve_base_dir(path_obj.parent)
            cache_dir = base_dir / "results_AAT" / "cache"
            if cache_dir.exists():
                cache_targets.append((path_obj, cache_dir))
                cache_dirs_found.add(cache_dir)

        if not cache_dirs_found:
            QMessageBox.information(
                self,
                "キャッシュクリア",
                "削除対象のキャッシュ保存先が見つかりませんでした。\nファイルを読み込んだ後に再度お試しください。",
            )
            logger.info("キャッシュクリア: 対象ディレクトリが見つかりませんでした")
            return

        # ユーザーに確認
        location_count = len(cache_dirs_found)
        reply = QMessageBox.question(
            self,
            "キャッシュクリア",
            f"検出した{location_count}か所のキャッシュ保存先にあるファイルを削除しますか？\nこの操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                total_deleted = 0
                for path_obj, cache_dir in cache_targets:
                    base_name = path_obj.stem
                    before_files = list(cache_dir.glob(f"{base_name}_*.pickle")) + list(
                        cache_dir.glob(f"{base_name}_*_raw.h5")
                    )
                    try:
                        delete_cache(str(path_obj))
                    except Exception as e:
                        logger.warning("キャッシュ削除中にエラー: %s", e)
                        continue
                    after_files = list(cache_dir.glob(f"{base_name}_*.pickle")) + list(
                        cache_dir.glob(f"{base_name}_*_raw.h5")
                    )
                    total_deleted += max(0, len(before_files) - len(after_files))

                if total_deleted > 0:
                    QMessageBox.information(
                        self,
                        "キャッシュクリア完了",
                        f"{len(cache_dirs_found)}か所のキャッシュ保存先から{total_deleted}個のキャッシュファイルを削除しました。",
                    )
                    logger.info(f"キャッシュクリア完了: {total_deleted}ファイル削除")
                else:
                    QMessageBox.information(self, "キャッシュクリア", "削除するキャッシュファイルがありませんでした。")

            except Exception as e:
                log_exception(e, "キャッシュクリア中にエラーが発生")
                QMessageBox.critical(self, "エラー", f"キャッシュクリア中にエラーが発生しました:\n{str(e)}")

    def closeEvent(self, event):
        """
        アプリケーション終了時の処理

        実行中のワーカーをすべて停止してから終了します。
        """
        # 実行中のワーカーがあれば安全に停止
        if hasattr(self, "workers") and self.workers:
            logger.info(f"アプリケーション終了: {len(self.workers)}個の実行中ワーカーを停止します")
            for worker in self.workers:
                if worker.isRunning():
                    try:
                        worker.quit_safely()
                    except Exception as e:
                        logger.error(f"ワーカー停止中にエラーが発生: {e}")

            # 全ワーカーのリストをクリア
            self.workers.clear()

        # matplotlibリソースのクリーンアップ
        try:
            self._clear_span_selectors()
            if hasattr(self, "figure"):
                plt.close(self.figure)
            plt.close("all")  # 全ての図を閉じる
            logger.info("matplotlibリソースをクリーンアップしました")
        except Exception as e:
            logger.warning(f"matplotlibクリーンアップ中にエラー: {e}")

        # 親クラスのcloseEventを呼び出し
        super().closeEvent(event)

    def on_select_range(self, xmin, xmax):
        """
        範囲選択時のコールバック関数

        Args:
            xmin (float): 選択範囲の最小値
            xmax (float): 選択範囲の最大値
        """
        # 何も選択されていない場合やドラッグ距離が小さすぎる場合は無視
        if xmax - xmin < 0.001:
            return

        # G-qualityモードの場合は処理しない
        if self.is_g_quality_mode:
            return

        selected_dataset = self.dataset_selector.currentText()
        if selected_dataset in self.processed_data:
            data = self.processed_data[selected_dataset]

            # Inner Capsuleのデータ
            inner_time = data["filtered_time"]
            inner_gravity = data["filtered_gravity_level_inner_capsule"]

            # Drag Shieldのデータ
            drag_time = data["filtered_adjusted_time"]
            drag_gravity = data["filtered_gravity_level_drag_shield"]

            # 選択範囲内のデータを抽出して統計計算
            self.calculate_selected_range_statistics(inner_time, inner_gravity, drag_time, drag_gravity, xmin, xmax)

            # 選択範囲をハイライト表示
            self.highlight_selected_range(xmin, xmax)

    def calculate_selected_range_statistics(self, inner_time, inner_gravity, drag_time, drag_gravity, xmin, xmax):
        """
        選択した範囲内のデータの統計情報を計算する

        Args:
            inner_time (pandas.Series): Inner Capsuleの時間データ
            inner_gravity (pandas.Series): Inner Capsuleの重力レベルデータ
            drag_time (pandas.Series): Drag Shieldの時間データ
            drag_gravity (pandas.Series): Drag Shieldの重力レベルデータ
            xmin (float): 選択範囲の開始時間
            xmax (float): 選択範囲の終了時間
        """
        from core.statistics import calculate_range_statistics

        # 選択範囲内のデータをフィルタリング
        inner_mask = (inner_time >= xmin) & (inner_time <= xmax)
        drag_mask = (drag_time >= xmin) & (drag_time <= xmax)

        # マスクが空の場合は何もしない
        if not inner_mask.any() and not drag_mask.any():
            QMessageBox.warning(self, "警告", "選択範囲内にデータがありません。")
            return

        # 統計情報を計算
        inner_stats = calculate_range_statistics(inner_gravity[inner_mask].values)
        drag_stats = calculate_range_statistics(drag_gravity[drag_mask].values)

        # 結果を表示するダイアログを呼び出し
        self.show_range_statistics_dialog(xmin, xmax, inner_stats, drag_stats)

    def highlight_selected_range(self, xmin, xmax):
        """
        選択した範囲をグラフ上でハイライト表示する

        Args:
            xmin (float): 選択範囲の開始時間
            xmax (float): 選択範囲の終了時間
        """
        # 既存のハイライトをクリア
        if hasattr(self, "highlight_patches"):
            for patch in self.highlight_patches:
                # 単純に非表示にする - パッチの削除は試みない
                patch.set_visible(False)

        self.highlight_patches = []

        # 現在のグラフ上で範囲を示すハイライトを追加
        axes = self.figure.get_axes()
        for ax in axes:
            patch = ax.axvspan(xmin, xmax, alpha=0.2, color="yellow")
            self.highlight_patches.append(patch)

        self.canvas.draw()

    def show_range_statistics_dialog(self, xmin, xmax, inner_stats, drag_stats):
        """
        選択範囲の統計情報を表示するダイアログを表示

        Args:
            xmin (float): 選択範囲の開始時間
            xmax (float): 選択範囲の終了時間
            inner_stats (dict): Inner Capsuleの統計情報
            drag_stats (dict): Drag Shieldの統計情報
        """
        from PySide6.QtWidgets import (
            QDialog,
            QLabel,
            QTableWidget,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("選択範囲の統計情報")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout()

        # 選択範囲の情報
        range_label = QLabel(f"選択範囲: {xmin:.4f}秒 ～ {xmax:.4f}秒 (範囲: {xmax - xmin:.4f}秒)")
        layout.addWidget(range_label)

        # 統計情報テーブル
        table = QTableWidget(6, 3)  # 6行3列
        table.setHorizontalHeaderLabels(["統計量", "Inner Capsule", "Drag Shield"])

        # テーブルデータ設定
        stats_items = [
            ("データポイント数", inner_stats["count"], drag_stats["count"]),
            ("平均値 (G)", inner_stats["mean"], drag_stats["mean"]),
            ("絶対値平均 (G)", inner_stats["abs_mean"], drag_stats["abs_mean"]),
            ("標準偏差 (G)", inner_stats["std"], drag_stats["std"]),
            ("最小値 (G)", inner_stats["min"], drag_stats["min"]),
            ("最大値 (G)", inner_stats["max"], drag_stats["max"]),
        ]

        for i, (name, inner_val, drag_val) in enumerate(stats_items):
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(
                i,
                1,
                QTableWidgetItem(f"{inner_val:.6f}" if inner_val is not None else "N/A"),
            )
            table.setItem(
                i,
                2,
                QTableWidgetItem(f"{drag_val:.6f}" if drag_val is not None else "N/A"),
            )

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()

    def _on_toolbar_action_triggered(self, action):
        """Matplotlibツールバーのアクションがトリガーされた時の処理"""
        # サブプロット設定ボタンなどが押された後、少し遅延させてダイアログを探しテーマを適用する
        QTimer.singleShot(100, self._apply_theme_to_matplotlib_dialogs)

    def _convert_checkboxes_to_toggles(self, dialog):
        """Matplotlibダイアログ内のQCheckBoxをToggleSwitch表示に差し替える"""
        for checkbox in dialog.findChildren(QCheckBox):
            # 既にToggleSwitchならスキップ
            if isinstance(checkbox, ToggleSwitch):
                continue

            parent_widget = checkbox.parentWidget()
            parent_layout = parent_widget.layout() if parent_widget else None
            if parent_layout is None:
                continue

            toggle = ToggleSwitch(dialog)
            toggle.setChecked(checkbox.isChecked())
            toggle.setEnabled(checkbox.isEnabled())
            toggle.setText(checkbox.text())
            toggle.setToolTip(checkbox.toolTip())

            # 双方向同期: 新しいトグル操作 -> 元チェックボックスに反映 -> 既存のシグナルも生きる
            toggle.toggled.connect(checkbox.setChecked)
            checkbox.toggled.connect(toggle.setChecked)

            # 位置を保ったまま差し替え
            parent_layout.replaceWidget(checkbox, toggle)
            checkbox.hide()

    def _apply_theme_to_matplotlib_dialogs(self):
        """Matplotlibが開いたダイアログにテーマを適用する"""
        from PySide6.QtWidgets import QDialog

        for widget in QApplication.topLevelWidgets():
            # タイトルで判別 (Matplotlibのバージョンによってタイトルが異なる可能性があるが、一般的には "Subplot Configuration")
            if isinstance(widget, QDialog) and ("Subplot" in widget.windowTitle() or "Figure" in widget.windowTitle()):
                # ダイアログ自体にスタイルシートを適用
                # 背景色とテキスト色を強制的に設定
                widget.setStyleSheet(
                    f"""
                    QDialog {{
                        background-color: {Colors.BG_PRIMARY};
                        color: {Colors.TEXT_PRIMARY};
                    }}
                    QLabel {{
                        color: {Colors.TEXT_PRIMARY};
                    }}
                    QLineEdit, QSpinBox, QDoubleSpinBox {{
                        background-color: {Colors.BG_TERTIARY};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 4px;
                        padding: 4px;
                        color: {Colors.TEXT_PRIMARY};
                    }}
                    QComboBox {{
                        background-color: {Colors.BG_TERTIARY};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 4px;
                        padding: 4px;
                        color: {Colors.TEXT_PRIMARY};
                    }}
                    QTabWidget::pane {{
                        border: 1px solid {Colors.BORDER};
                    }}
                    QTabBar::tab {{
                        background: {Colors.BG_SECONDARY};
                        color: {Colors.TEXT_PRIMARY};
                        padding: 8px 12px;
                        border: 1px solid {Colors.BORDER};
                        border-bottom: none;
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                    }}
                    QTabBar::tab:selected {{
                        background: {Colors.BG_TERTIARY};
                        border-bottom: 1px solid {Colors.BG_TERTIARY};
                    }}
                    {get_toggle_checkbox_styles()}
                    """
                )
                self._convert_checkboxes_to_toggles(widget)
