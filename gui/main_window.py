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
from matplotlib import font_manager
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt6.QtCore import QMutex, Qt
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

        # 進行度バーの追加
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

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

    # ------------------------------------------------
    # ファイル処理関連メソッド
    # ------------------------------------------------

    def select_and_process_file(self):
        """
        CSVファイルを選択し、データを処理する

        ファイル選択ダイアログを表示し、選択されたCSVファイルを
        読み込んで処理します。CSVファイル内の列が判断できない場合は
        列選択ダイアログを表示します。
        """
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "CSVファイルを選択", "", "CSV files (*.csv)")
            if not file_paths:
                logger.info("ファイルは選択されませんでした")
                return

            logger.info(f"選択されたファイル数: {len(file_paths)}")
            self.status_label.setText("処理中...")
            QApplication.processEvents()

            for file_path in file_paths:
                logger.info(f"ファイル処理開始: {file_path}")
                file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]

                # データの読み込みと処理
                try:
                    # データの読み込みを試みる
                    time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time = load_and_process_data(file_path, self.config)
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
                                time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time = load_and_process_data(
                                    file_path, temp_config
                                )

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
                filtered_time, filtered_gravity_level_inner_capsule, filtered_gravity_level_drag_shield, filtered_adjusted_time, end_index = (
                    filter_data(time, gravity_level_inner_capsule, gravity_level_drag_shield, adjusted_time, self.config)
                )

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
                }
                self.file_paths[file_name_without_ext] = file_path
                logger.info(f"データ処理完了: {file_name_without_ext}")

                # グラフの作成と保存
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

                # 統計情報の計算と保存
                min_mean_inner_capsule, min_time_inner_capsule, min_std_inner_capsule = calculate_statistics(
                    filtered_gravity_level_inner_capsule, filtered_time, self.config
                )
                min_mean_drag_shield, min_time_drag_shield, min_std_drag_shield = calculate_statistics(
                    filtered_gravity_level_drag_shield, filtered_adjusted_time, self.config
                )

                # データのエクスポート
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
                    self.config,  # 設定情報を渡す
                )
                logger.info(f"データエクスポート完了: {file_name_without_ext}")

            # UI更新
            self.update_table()
            self.update_dataset_selector()
            self.status_label.setText("処理が完了しました")
            logger.info("すべてのファイルの処理が完了しました")

        except Exception as e:
            log_exception(e, "ファイル処理中に例外が発生")
            self.status_label.setText("エラーが発生しました")
            QMessageBox.critical(self, "エラー", str(e))

    # ------------------------------------------------
    # UI更新関連メソッド
    # ------------------------------------------------

    def update_dataset_selector(self):
        """
        データセットセレクターのコンボボックスを更新する
        """
        self.dataset_selector.clear()
        if self.is_comparing:
            self.dataset_selector.addItem("複数グラフ比較")
        else:
            dataset_names = list(self.processed_data.keys())
            self.dataset_selector.addItems(dataset_names)

    def update_selected_dataset(self):
        """
        選択されたデータセットに応じてグラフを更新する
        """
        if self.is_comparing:
            self.plot_comparison()
        else:
            selected_dataset = self.dataset_selector.currentText()
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
                logger.warning(f"選択されたデータセットが見つかりません: {selected_dataset}")

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

        # グラフの右下にAAT-v8を追加
        ax.text(0.98, 0.02, "AAT-v8", transform=ax.transAxes, fontsize=8, verticalalignment="bottom", horizontalalignment="right")

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

        # グラフの右下にAAT-v8を追加
        ax.text(0.98, 0.02, "AAT-v8", transform=ax.transAxes, fontsize=8, verticalalignment="bottom", horizontalalignment="right")

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

        # グラフの右下にAAT-v8を追加
        ax.text(0.98, 0.02, "AAT-v8", transform=ax.transAxes, fontsize=8, verticalalignment="bottom", horizontalalignment="right")

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

        # グラフの右下にAAT-v8を追加
        ax.text(0.98, 0.02, "AAT-v8", transform=ax.transAxes, fontsize=8, verticalalignment="bottom", horizontalalignment="right")

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
            self.g_quality_mode_button.setText("G-quality評価モード実行中")
            self.g_quality_mode_button.setEnabled(False)
            self.perform_g_quality_analysis_for_all_datasets()
        else:
            self.g_quality_mode_button.setText("G-quality評価モード")
            self.g_quality_mode_button.setEnabled(True)
            self.return_to_normal_mode()

        self.update_button_visibility()
        if self.is_comparing:
            self.plot_comparison()

    def return_to_normal_mode(self):
        """
        通常モードに戻る
        """
        # スレッドを停止
        for worker in self.workers:
            worker.stop()
            worker.wait()
        self.workers.clear()

        self.g_quality_data = None  # G-qualityデータをクリア
        self.update_selected_dataset()  # 通常モードのグラフを表示
        self.update_table()
        self.update_button_visibility()

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

        Args:
            g_quality_data (list): G-quality解析結果
            file_name (str): ファイル名
            original_file_path (str): 元のファイルパス
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

        # 結果をExcelファイルに出力
        if original_file_path:
            export_path = export_g_quality_data(g_quality_data, original_file_path)
            if export_path:
                QMessageBox.information(self, "保存完了", f"G-quality解析の結果が {export_path} に追加されました")

        # グラフを描画
        self.plot_g_quality_data(g_quality_data, file_name)

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
        ウィンドウが閉じられる前に呼ばれるイベントハンドラ

        実行中のすべてのワーカースレッドを適切に停止させる

        Args:
            event (QCloseEvent): クローズイベント
        """
        logger.info("アプリケーションを終了します")

        # 実行中のスレッドをすべて停止
        for worker in self.workers[:]:  # リストのコピーを使用
            if worker.isRunning():
                logger.debug("実行中のワーカースレッドを停止します")
                worker.stop()
                worker.wait()

        self.workers.clear()
        event.accept()
