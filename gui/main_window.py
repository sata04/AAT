#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メインウィンドウモジュール

アプリケーションのメインウィンドウとその機能を定義します。
グラフ表示、データテーブル、ファイル処理、解析機能などの
ユーザーインターフェースを提供します。
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.widgets import SpanSelector
from PyQt6.QtCore import QMutex, Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.config import load_config, save_config
from core.data_processor import filter_data, load_and_process_data
from core.export import export_data, export_g_quality_data
from core.logger import get_logger, log_exception
from core.statistics import calculate_statistics
from gui.column_selector_dialog import ColumnSelectorDialog
from gui.settings_dialog import SettingsDialog
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

        # 日本語フォント設定
        self._setup_japanese_font()

        # ウィンドウの基本設定
        self.setWindowTitle("Gravity Level Analysis")
        self.setGeometry(100, 100, 1200, 800)

        # UI要素の初期化
        self._setup_ui()

        # データと状態の初期化
        self._initialize_data()

        logger.info("メインウィンドウの初期化が完了しました")

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
        except Exception as e:
            log_exception(e, "フォント設定中にエラー")
            # フォント設定に失敗した場合はデフォルトフォントを使用
            plt.rcParams["font.family"] = "sans-serif"
            logger.info("デフォルトフォントにフォールバック: sans-serif")

    def _setup_ui(self):
        """
        UIコンポーネントを初期化する
        """
        # メインウィジェットとレイアウトの設定
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # ステータスラベルの追加
        self.status_label = QLabel("ファイルを選択してください")
        self.main_layout.addWidget(self.status_label)

        # 処理状況表示ラベルの追加
        self.processing_status_label = QLabel("")
        self.processing_status_label.setVisible(False)
        self.main_layout.addWidget(self.processing_status_label)

        # ボタンレイアウトの設定
        button_layout = QHBoxLayout()

        # ファイル選択ボタン
        select_button = QPushButton("CSVファイルを選択")
        select_button.clicked.connect(self.select_and_process_file)
        button_layout.addWidget(select_button)

        # 比較モードボタン
        self.compare_button = QPushButton("複数ファイルを比較")
        self.compare_button.clicked.connect(self.toggle_comparison)
        button_layout.addWidget(self.compare_button)

        # G-quality評価モードボタン
        self.g_quality_mode_button = QPushButton("G-quality評価モード")
        self.g_quality_mode_button.setCheckable(True)
        self.g_quality_mode_button.clicked.connect(self.toggle_g_quality_mode)
        button_layout.addWidget(self.g_quality_mode_button)

        # 進行度バーのレイアウト
        progress_layout = QVBoxLayout()

        # ファイル単位の進捗バー
        self.file_progress_label = QLabel("ファイル処理進捗:")
        self.file_progress_label.setVisible(False)
        progress_layout.addWidget(self.file_progress_label)

        self.file_progress_bar = QProgressBar(self)
        self.file_progress_bar.setVisible(False)
        progress_layout.addWidget(self.file_progress_bar)

        # 全体の進捗バー
        self.progress_label = QLabel("全体進捗:")
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.main_layout.addLayout(progress_layout)

        # 全データ表示ボタン
        self.show_all_button = QPushButton("全体を表示")
        self.show_all_button.setCheckable(True)
        self.show_all_button.clicked.connect(self.toggle_show_all_data)
        button_layout.addWidget(self.show_all_button)

        # 設定ボタン
        settings_button = QPushButton("設定")
        settings_button.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_button)

        self.main_layout.addLayout(button_layout)

        # グラフとテーブルを含むスプリッターの設定
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_layout.addWidget(splitter)

        # グラフウィジェットの設定
        self.figure = plt.figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        graph_layout.addWidget(self.toolbar)
        graph_layout.addWidget(self.canvas)
        splitter.addWidget(graph_widget)

        # データセット選択用コンボボックス
        self.dataset_selector = QComboBox()
        self.dataset_selector.currentIndexChanged.connect(self.update_selected_dataset)
        button_layout.addWidget(self.dataset_selector)

        # データテーブルの設定
        self.table = QTableWidget()
        splitter.addWidget(self.table)

        # 範囲選択機能の変数を初期化
        self.span_selectors = []

    def _initialize_data(self):
        """
        データと状態変数を初期化する
        """
        # データ保存用辞書
        self.processed_data = {}

        # 設定の読み込み
        self.config = load_config()

        # 各種フラグの初期化
        self.is_comparing = False
        self.is_g_quality_mode = False
        self.is_showing_all_data = False
        self.g_quality_data = None
        self.is_g_quality_analysis_running = False

        # ワーカースレッド配列の初期化
        self.workers = []

        # ワーカー操作用のミューテックス
        self.worker_mutex = QMutex()

        # ファイル名とパスのマッピング
        self.file_paths = {}  # ファイル名とパスを保存する辞書

    def _suppress_qt_messages(self):
        """
        特定のQtメッセージを抑制する
        """
        try:
            from PyQt6.QtCore import QtMsgType, qInstallMessageHandler

            def message_handler(msg_type, context, message):
                # Layer-backingのメッセージを抑制
                if "Layer-backing is always enabled" in message:
                    return
                # その他のメッセージは標準のハンドラで処理
                if msg_type == QtMsgType.QtWarningMsg:
                    logger.warning(f"Qt Warning: {message}")
                elif msg_type == QtMsgType.QtCriticalMsg:
                    logger.error(f"Qt Critical: {message}")
                elif msg_type == QtMsgType.QtFatalMsg:
                    logger.critical(f"Qt Fatal: {message}")

            # カスタムメッセージハンドラを設定
            qInstallMessageHandler(message_handler)
            logger.info("Qtメッセージハンドラを設定しました")
        except Exception as e:
            log_exception(e, "Qtメッセージハンドラの設定に失敗")

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
            self.progress_label.setText("全体進捗:")
            self.progress_label.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(total_files)

            # ファイル進捗表示の初期化
            self.file_progress_label.setText("ファイル処理進捗:")
            self.file_progress_label.setVisible(True)
            self.file_progress_bar.setVisible(True)
            self.file_progress_bar.setValue(0)
            self.file_progress_bar.setMaximum(100)

            # 処理状況表示の初期化
            self.processing_status_label.setVisible(True)
            self.processing_status_label.setText("処理を開始します...")

            QApplication.processEvents()

            # キャッシュモジュールをインポート
            from core.cache_manager import generate_cache_id, has_valid_cache, load_from_cache, save_to_cache

            for file_idx, file_path in enumerate(file_paths):
                logger.info(f"ファイル処理開始 ({file_idx + 1}/{total_files}): {file_path}")
                file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]

                # 進捗更新
                self.progress_bar.setValue(file_idx)
                self.processing_status_label.setText(f"処理中: {file_name_without_ext} ({file_idx + 1}/{total_files})")
                QApplication.processEvents()

                # キャッシュの確認
                if self.config.get("use_cache", True):
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
                            self.processing_status_label.setText(f"キャッシュからデータを読み込み中... ({file_idx + 1}/{total_files})")
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
                                if self.config.get("auto_calculate_g_quality", True) and "g_quality_data" not in cached_data:
                                    self.processing_status_label.setText(f"G-quality評価を計算中... ({file_idx + 1}/{total_files})")
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
                    time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time = load_and_process_data(file_path, self.config)
                    self.file_progress_bar.setValue(40)
                    QApplication.processEvents()

                except ValueError as e:
                    # 特定のエラーメッセージの場合は列選択ダイアログを表示
                    if len(e.args) > 1 and e.args[0] == "必要な列が見つかりません。列の選択が必要です。":
                        # 時間列と加速度列の候補を取得
                        time_columns = e.args[1]
                        accel_columns = e.args[2]

                        if not time_columns:
                            QMessageBox.critical(self, "エラー", "CSVファイルに時間列の候補が見つかりませんでした。")
                            continue

                        if len(accel_columns) < 2:
                            QMessageBox.critical(self, "エラー", "CSVファイルに加速度列の候補が十分にありません。少なくとも2つの加速度列が必要です。")
                            continue

                        # 列選択ダイアログを表示
                        dialog = ColumnSelectorDialog(time_columns, accel_columns, self)
                        if dialog.exec():
                            # ダイアログから選択された列を取得
                            time_column, inner_column, drag_column = dialog.get_selected_columns()

                            # 一時的に設定を上書き
                            temp_config = self.config.copy()
                            temp_config["time_column"] = time_column
                            temp_config["acceleration_column_inner_capsule"] = inner_column
                            temp_config["acceleration_column_drag_shield"] = drag_column

                            # 再度データの読み込みを試みる
                            try:
                                # 元のCSVデータを読み込む
                                raw_data = pd.read_csv(file_path)
                                self.file_progress_bar.setValue(20)
                                QApplication.processEvents()

                                time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time = load_and_process_data(
                                    file_path, temp_config
                                )
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
                                    self.config.update(
                                        {
                                            "time_column": time_column,
                                            "acceleration_column_inner_capsule": inner_column,
                                            "acceleration_column_drag_shield": drag_column,
                                        }
                                    )
                                    save_config(self.config)
                                    logger.info("列設定を保存しました")
                                else:
                                    # 保存しない場合でも、このファイルの処理には選択した列情報を使用するために
                                    # 現在の処理中ではtemp_configを使い続ける
                                    logger.info("列設定は一時的に使用されますが、保存はしません")
                            except Exception as e2:
                                log_exception(e2, "選択された列でのデータ読み込み中にエラーが発生")
                                QMessageBox.critical(self, "エラー", f"選択された列でのデータ読み込みに失敗しました: {str(e2)}")
                                continue
                        else:
                            # ダイアログがキャンセルされた場合は次のファイルへ
                            logger.info("列選択がキャンセルされました")
                            continue
                    else:
                        # その他のエラーはそのまま表示
                        raise

                # データのフィルタリング
                self.processing_status_label.setText(f"データをフィルタリング中... ({file_idx + 1}/{total_files})")
                QApplication.processEvents()

                filtered_time, filtered_gravity_level_inner_capsule, filtered_gravity_level_drag_shield, filtered_adjusted_time, end_index = (
                    filter_data(time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time, self.config)
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
                }
                self.file_paths[file_name_without_ext] = file_path
                logger.info(f"データ処理完了: {file_name_without_ext}")

                # データをキャッシュに保存
                if self.config.get("use_cache", True):
                    self.processing_status_label.setText(f"データをキャッシュに保存中... ({file_idx + 1}/{total_files})")
                    QApplication.processEvents()

                    cache_id = generate_cache_id(file_path, self.config)
                    save_to_cache(self.processed_data[file_name_without_ext], file_path, cache_id, self.config)

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

                min_mean_inner_capsule, min_time_inner_capsule, min_std_inner_capsule = calculate_statistics(
                    filtered_gravity_level_inner_capsule, filtered_time, self.config
                )
                min_mean_drag_shield, min_time_drag_shield, min_std_drag_shield = calculate_statistics(
                    filtered_gravity_level_drag_shield, filtered_adjusted_time, self.config
                )
                self.file_progress_bar.setValue(80)
                QApplication.processEvents()

                # データエクスポート用の設定を準備
                # 列選択ダイアログで選択した場合は、その選択情報を使用する
                export_config = self.config.copy()
                if "temp_config" in locals():
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
                )
                logger.info(f"データエクスポート完了: {file_name_without_ext}")
                self.file_progress_bar.setValue(90)
                QApplication.processEvents()

                # 自動G-quality評価がオンの場合は計算
                if self.config.get("auto_calculate_g_quality", True):
                    self.calculate_g_quality_for_dataset(file_name_without_ext, file_idx, total_files)

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
            QTimer.singleShot(3000, self.hide_progress_bars)

        except Exception as e:
            log_exception(e, "ファイル処理中に例外が発生")
            self.status_label.setText("エラーが発生しました")
            self.processing_status_label.setText(f"エラー: {str(e)}")
            QMessageBox.critical(self, "エラー", str(e))

    def calculate_g_quality_for_dataset(self, dataset_name, file_idx, total_files):
        """
        指定されたデータセットに対してG-quality評価を行う

        Args:
            dataset_name (str): データセット名
            file_idx (int): ファイルインデックス
            total_files (int): 総ファイル数
        """
        if dataset_name not in self.processed_data:
            logger.warning(f"データセットが見つかりません: {dataset_name}")
            return

        data = self.processed_data[dataset_name]
        original_file_path = self.file_paths.get(dataset_name)

        # G-quality評価が既に存在するかチェック
        if "g_quality_data" in data:
            logger.info(f"G-quality評価は既に存在します: {dataset_name}")
            return

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
            save_to_cache(self.processed_data[dataset_name], original_file_path, cache_id, self.config)

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

        # シグナルのブロックを解除
        self.dataset_selector.blockSignals(False)

        # データセットが存在する場合に最初のアイテムを選択
        if self.dataset_selector.count() > 0:
            self.dataset_selector.setCurrentIndex(0)
            # 明示的にデータセットの更新メソッドを呼び出す
            self.update_selected_dataset()

    def update_selected_dataset(self):
        """
        選択されたデータセットに応じてグラフを更新する
        """
        try:
            if self.is_comparing:
                self.plot_comparison()
            else:
                selected_dataset = self.dataset_selector.currentText()

                # 「データがありません」のプレースホルダーの場合は何もしない
                if selected_dataset == "データがありません":
                    return

                if selected_dataset in self.processed_data:
                    data = self.processed_data[selected_dataset]
                    if self.is_g_quality_mode and "g_quality_data" in data:
                        self.plot_g_quality_data(data["g_quality_data"], selected_dataset)
                    elif self.is_showing_all_data:
                        self.show_all_data(data)
                    else:
                        self.plot_gravity_level(
                            data["filtered_time"],
                            data["filtered_adjusted_time"],
                            data["filtered_gravity_level_inner_capsule"],
                            data["filtered_gravity_level_drag_shield"],
                            self.config,
                            selected_dataset,
                            "",
                        )
                else:
                    logger.debug(f"選択されたデータセットが見つかりません: {selected_dataset}")
                    # ユーザーにはエラーを表示しない

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
                data["filtered_gravity_level_inner_capsule"], data["filtered_time"], self.config
            )
            min_mean_drag_shield, min_time_drag_shield, min_std_drag_shield = calculate_statistics(
                data["filtered_gravity_level_drag_shield"], data["filtered_adjusted_time"], self.config
            )

            # テーブルにデータを設定（Noneチェックを追加）
            self.table.setItem(row, 0, QTableWidgetItem(file_name))
            self.table.setItem(row, 1, QTableWidgetItem(f"{min_time_inner_capsule:.3f}" if min_time_inner_capsule is not None else "None"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{min_mean_inner_capsule:.4f}" if min_mean_inner_capsule is not None else "None"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{min_std_inner_capsule:.4f}" if min_std_inner_capsule is not None else "None"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{min_time_drag_shield:.3f}" if min_time_drag_shield is not None else "None"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{min_mean_drag_shield:.4f}" if min_mean_drag_shield is not None else "None"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{min_std_drag_shield:.4f}" if min_std_drag_shield is not None else "None"))

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
            self.table.setItem(row, 1, QTableWidgetItem(f"{window_size:.3f}" if window_size is not None else "None"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{min_time_inner_capsule:.3f}" if min_time_inner_capsule is not None else "None"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{min_mean_inner_capsule:.4f}" if min_mean_inner_capsule is not None else "None"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{min_std_inner_capsule:.4f}" if min_std_inner_capsule is not None else "None"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{min_time_drag_shield:.3f}" if min_time_drag_shield is not None else "None"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{min_mean_drag_shield:.4f}" if min_mean_drag_shield is not None else "None"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{min_std_drag_shield:.4f}" if min_std_drag_shield is not None else "None"))

        self.table.resizeColumnsToContents()

    # ------------------------------------------------
    # グラフ表示関連メソッド
    # ------------------------------------------------

    def plot_gravity_level(
        self, time, adjusted_time, gravity_level_inner_capsule, gravity_level_drag_shield, config, file_name_without_ext, original_file_path
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
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Inner Capsuleは元の時間で、Drag Shieldは調整後の時間でプロット
        ax.plot(time, gravity_level_inner_capsule, label=f"{file_name_without_ext} (Inner Capsule)", linewidth=0.8)
        ax.plot(adjusted_time, gravity_level_drag_shield, label=f"{file_name_without_ext} (Drag Shield)", linewidth=0.8)

        ax.set_ylim(config["ylim_min"], config["ylim_max"])

        # x軸の範囲を0から設定
        ax.set_xlim(0, max(time.max(), adjusted_time.max()))

        ax.set_title(f"The Gravity Level {file_name_without_ext}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Gravity Level (G)")
        ax.legend()
        ax.grid(True)

        # グラフの右下にAAT-v9.0.0を追加
        ax.text(0.98, 0.02, "AAT-v9.0.0", transform=ax.transAxes, fontsize=8, verticalalignment="bottom", horizontalalignment="right")

        # 範囲選択機能を追加
        # 既存のSpanSelectorをクリア
        self.span_selectors.clear()

        # SpanSelectorを追加
        span = SpanSelector(
            ax,
            self.on_select_range,
            "horizontal",
            useblit=True,
            props=dict(alpha=0.3, facecolor="tab:blue"),
            interactive=True,
            drag_from_anywhere=True,
        )
        self.span_selectors.append(span)

        self.canvas.draw()

        # グラフの保存
        if original_file_path:
            # CSVファイルのディレクトリを取得
            csv_dir = os.path.dirname(original_file_path)

            # 結果ディレクトリとグラフディレクトリのパスを生成
            results_dir = os.path.join(csv_dir, "results_AAT")
            graphs_dir = os.path.join(results_dir, "graphs")

            # ディレクトリが存在しない場合は作成
            os.makedirs(graphs_dir, exist_ok=True)

            # グラフ保存パスを設定 (ファイル名_gl.png形式)
            graph_path = os.path.join(graphs_dir, f"{file_name_without_ext}_gl.png")
            self.figure.savefig(graph_path, dpi=300, bbox_inches="tight")
            logger.info(f"グラフを保存しました: {graph_path}")
            return graph_path

        return None

    def plot_comparison(self):
        """
        複数のデータセットを比較するグラフを描画する
        """
        logger.info("比較グラフのプロット開始")
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # カラーマップを使用して、各データセットに異なる色を割り当てる
        colors = plt.cm.rainbow(np.linspace(0, 1, len(self.processed_data) * 2))
        color_index = 0

        for file_name, data in self.processed_data.items():
            if self.is_g_quality_mode:
                if "g_quality_data" in data:
                    # G-quality モードでの比較プロット
                    (
                        window_sizes,
                        min_times_inner_capsule,
                        min_means_inner_capsule,
                        min_stds_inner_capsule,
                        min_times_drag_shield,
                        min_means_drag_shield,
                        min_stds_drag_shield,
                    ) = zip(*data["g_quality_data"])
                    ax.plot(window_sizes, min_means_inner_capsule, label=f"{file_name} (Inner Capsule)", color=colors[color_index])
                    color_index += 1
                    ax.plot(window_sizes, min_means_drag_shield, label=f"{file_name} (Drag Shield)", color=colors[color_index])
                    color_index += 1
            else:
                if self.is_showing_all_data:
                    # 全データを表示（マイナスの時間も含む）
                    ax.plot(
                        data["time"],
                        data["gravity_level_inner_capsule"],
                        label=f"{file_name} (Inner Capsule)",
                        linewidth=0.8,
                        color=colors[color_index],
                    )
                    color_index += 1
                    ax.plot(
                        data["adjusted_time"],
                        data["gravity_level_drag_shield"],
                        label=f"{file_name} (Drag Shield)",
                        linewidth=0.8,
                        color=colors[color_index],
                    )
                    color_index += 1
                else:
                    # フィルタリングされたデータの表示
                    ax.plot(
                        data["filtered_time"],
                        data["filtered_gravity_level_inner_capsule"],
                        label=f"{file_name} (Inner Capsule)",
                        linewidth=0.8,
                        color=colors[color_index],
                    )
                    color_index += 1
                    ax.plot(
                        data["filtered_adjusted_time"],
                        data["filtered_gravity_level_drag_shield"],
                        label=f"{file_name} (Drag Shield)",
                        linewidth=0.8,
                        color=colors[color_index],
                    )
                    color_index += 1

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

        ax.legend()
        ax.grid(True)

        # グラフの右下にAAT-v9.0.0を追加
        ax.text(0.98, 0.02, "AAT-v9.0.0", transform=ax.transAxes, fontsize=8, verticalalignment="bottom", horizontalalignment="right")

        # 比較モードではSpanSelectorを追加しない（選択範囲の統計計算を無効化）
        self.span_selectors.clear()

        self.canvas.draw()

    def plot_g_quality_data(self, g_quality_data, file_name):
        """
        G-quality解析データをグラフ表示する

        Args:
            g_quality_data (list): G-quality解析結果のリスト
            file_name (str): ファイル名
        """
        # original_file_pathをファイルパス辞書から取得
        original_file_path = self.file_paths.get(file_name)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # データをアンパック
        (
            window_sizes,
            min_times_inner_capsule,
            min_means_inner_capsule,
            min_stds_inner_capsule,
            min_times_drag_shield,
            min_means_drag_shield,
            min_stds_drag_shield,
        ) = zip(*g_quality_data)

        ax.plot(window_sizes, min_means_inner_capsule, color="darkblue", label="Inner Capsule: Mean Gravity Level")
        ax.plot(window_sizes, min_means_drag_shield, color="red", label="Drag Shield: Mean Gravity Level")
        ax.set_xlabel("Window Size (s)")
        ax.set_ylabel("Mean Gravity Level (G)")

        ax2 = ax.twinx()
        ax2.plot(window_sizes, min_stds_inner_capsule, color="dodgerblue", label="Inner Capsule: Standard Deviation")
        ax2.plot(window_sizes, min_stds_drag_shield, color="violet", label="Drag Shield: Standard Deviation")
        ax2.set_ylabel("Standard Deviation (G)")

        ax.set_title(f"G-quality Analysis - {file_name}")
        ax.grid(True)
        ax.legend(loc="upper left")
        ax2.legend(loc="upper right")

        self.figure.tight_layout()

        # グラフの右下にAAT-v9.0.0を追加
        ax.text(0.98, 0.02, "AAT-v9.0.0", transform=ax.transAxes, fontsize=8, verticalalignment="bottom", horizontalalignment="right")

        # SpanSelectorをクリア（G-qualityモードでは選択範囲機能を無効化）
        self.span_selectors.clear()

        # グラフ保存パスを設定 (ファイル名_gq.png形式)
        csv_dir = os.path.dirname(original_file_path)
        results_dir = os.path.join(csv_dir, "results_AAT")
        graphs_dir = os.path.join(results_dir, "graphs")
        os.makedirs(graphs_dir, exist_ok=True)
        graph_path = os.path.join(graphs_dir, f"{file_name}_gq.png")
        self.figure.savefig(graph_path, dpi=300, bbox_inches="tight")
        logger.info(f"G-qualityグラフを保存しました: {graph_path}")

        self.canvas.draw()
        return graph_path

    def show_all_data(self, data):
        """
        フィルタリング前のすべてのデータをグラフ表示する

        Args:
            data (dict): 表示するデータ
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # 全データを表示（マイナスの時間も含む）
        ax.plot(data["time"], data["gravity_level_inner_capsule"], color="blue", linewidth=0.8, label="Inner Capsule")
        ax.plot(data["adjusted_time"], data["gravity_level_drag_shield"], color="red", linewidth=0.8, label="Drag Shield")

        # トリミング範囲を強調表示
        # Inner Capsuleの範囲
        ax.axvspan(0, data["filtered_time"].iloc[-1], alpha=0.1, color="blue", label="Inner Capsule Range")
        # Drag Shieldの範囲
        ax.axvspan(0, data["filtered_adjusted_time"].iloc[-1], alpha=0.1, color="red", label="Drag Shield Range")

        ax.set_title(f"The Gravity Level {self.dataset_selector.currentText()} (All Data)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Gravity Level (G)")
        ax.legend()
        ax.grid(True)

        # グラフの右下にAAT-v9.0.0を追加
        ax.text(0.98, 0.02, "AAT-v9.0.0", transform=ax.transAxes, fontsize=8, verticalalignment="bottom", horizontalalignment="right")

        # 全体表示モードではSpanSelectorを追加しない（選択範囲の統計計算を無効化）
        self.span_selectors.clear()

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

    def start_comparison(self):
        """
        比較モードを開始する
        """
        if len(self.processed_data) < 2:
            logger.warning("比較モードには少なくとも2つのデータセットが必要です")
            QMessageBox.warning(self, "警告", "比較するには少なくとも2つのファイルが必要です。")
            return

        self.is_comparing = True
        self.compare_button.setText("個別グラフに戻る")
        self.update_dataset_selector()
        self.update_button_visibility()
        self.plot_comparison()
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

    # ------------------------------------------------
    # G-quality解析関連メソッド
    # ------------------------------------------------

    def perform_g_quality_analysis(
        self, filtered_time, filtered_gravity_level_inner_capsule, filtered_gravity_level_drag_shield, file_name, original_file_path
    ):
        """
        指定されたデータに対してG-quality解析を実行する

        Args:
            filtered_time (pandas.Series): フィルタリングされた時間データ
            filtered_gravity_level_inner_capsule (pandas.Series): Inner Capsuleの重力レベル
            filtered_gravity_level_drag_shield (pandas.Series): Drag Shieldの重力レベル
            file_name (str): ファイル名
            original_file_path (str): 元のファイルパス
        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # ワーカースレッドの作成と開始
        worker = GQualityWorker(filtered_time, filtered_gravity_level_inner_capsule, filtered_gravity_level_drag_shield, self.config)
        self.workers.append(worker)
        worker.progress.connect(self.update_progress)
        worker.finished.connect(lambda result: self.on_g_quality_analysis_finished(result, file_name, original_file_path))
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
                QMessageBox.information(self, "保存完了", f"G-quality解析の結果が {export_path} に追加されました")

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
            save_config(self.config)
            QMessageBox.information(self, "設定保存", "設定が保存されました。")

    def closeEvent(self, event):
        """
        アプリケーション終了時の処理

        実行中のワーカーをすべて停止してから終了します。
        """
        # 実行中のワーカーがあれば停止
        if hasattr(self, "workers") and self.workers:
            logger.info(f"アプリケーション終了: {len(self.workers)}個の実行中ワーカーを停止します")
            for worker in self.workers:
                if worker.isRunning():
                    worker.stop()
                    worker.wait(1000)  # 最大1秒待機

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
        if not inner_mask.any() or not drag_mask.any():
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
        from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

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
            table.setItem(i, 1, QTableWidgetItem(f"{inner_val:.6f}" if inner_val is not None else "N/A"))
            table.setItem(i, 2, QTableWidgetItem(f"{drag_val:.6f}" if drag_val is not None else "N/A"))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()
