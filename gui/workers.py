#!/usr/bin/env python3
"""
ワーカースレッドモジュール

UIブロックを防止するためのバックグラウンド処理用のワーカースレッドを提供します。
主にG-quality解析などの時間のかかる処理を非同期で実行します。
"""

import numpy as np
from PySide6.QtCore import QThread, Signal

from core.logger import get_logger, log_exception
from core.statistics import calculate_statistics

# モジュール用のロガーを初期化
logger = get_logger("workers")


class GQualityWorker(QThread):
    """
    G-quality解析を行うワーカースレッド

    異なるウィンドウサイズでの重力レベルの標準偏差を計算し、
    最適な微小重力環境を特定するための分析を非同期で実行します。
    """

    # シグナル定義
    progress = Signal(int)  # 進捗更新用シグナル (0-100%)
    status_update = Signal(str)  # 状態更新用シグナル
    overall_progress = Signal(int, int)  # 全体の進捗用シグナル (現在のファイル, 総ファイル数)
    finished = Signal(list)  # 結果送信用シグナル

    def __init__(
        self,
        filtered_time,
        filtered_gravity_level_inner_capsule,
        filtered_gravity_level_drag_shield,
        config,
        file_index=0,
        total_files=1,
        filtered_adjusted_time=None,
    ):
        """
        コンストラクタ

        Args:
            filtered_time (pandas.Series): フィルタリングされた時間データ
            filtered_gravity_level_inner_capsule (pandas.Series): カプセル内の重力レベルデータ
            filtered_gravity_level_drag_shield (pandas.Series): ドラッグシールドの重力レベルデータ
            config (dict): 設定情報
            file_index (int, optional): 現在処理中のファイルのインデックス。デフォルトは0。
            total_files (int, optional): 処理する総ファイル数。デフォルトは1。
            filtered_adjusted_time (pandas.Series, optional): ドラッグシールド用のフィルタリングされた調整時間データ
        """
        super().__init__()
        self.filtered_time = filtered_time
        self.filtered_gravity_level_inner_capsule = filtered_gravity_level_inner_capsule
        self.filtered_gravity_level_drag_shield = filtered_gravity_level_drag_shield
        self.filtered_adjusted_time = filtered_adjusted_time if filtered_adjusted_time is not None else filtered_time
        self.config = config
        self.file_index = file_index
        self.total_files = total_files
        self.is_running = True

    def get_results(self):
        """
        処理結果を返す

        Returns:
            list: G-quality解析結果
        """
        return getattr(self, "g_quality_data", [])

    def stop(self):
        """
        ワーカーの実行を安全に停止する
        """
        logger.info("G-quality解析の停止要求を受信")
        self.is_running = False

    def quit_safely(self):
        """
        スレッドを安全に終了する
        """
        self.stop()
        self.quit()
        if not self.wait(2000):  # 2秒待機
            logger.warning("ワーカースレッドの正常終了がタイムアウトしました")
            self.terminate()
            if not self.wait(1000):  # さらに1秒待機
                logger.error("ワーカースレッドの強制終了に失敗しました")

    def run(self):
        """
        スレッドの実行メソッド

        異なるウィンドウサイズでの重力レベル統計を計算し、
        結果をリストとして返します。進捗状況は進捗シグナルを通じて通知します。
        """
        try:
            # データサイズの事前チェック
            data_length_inner = len(self.filtered_gravity_level_inner_capsule)
            data_length_drag = len(self.filtered_gravity_level_drag_shield)
            sampling_rate = self.config.get("sampling_rate", 1000)
            has_inner = data_length_inner > 0
            has_drag = data_length_drag > 0

            logger.info(
                f"G-quality解析開始: inner_capsule={data_length_inner}, "
                f"drag_shield={data_length_drag}, sampling_rate={sampling_rate}"
            )

            g_quality_data = []
            # 設定から開始サイズ、終了サイズ、ステップサイズを取得してウィンドウサイズの配列を生成
            window_sizes = np.arange(
                self.config["g_quality_start"],
                self.config["g_quality_end"] + self.config["g_quality_step"],
                self.config["g_quality_step"],
            )
            total_steps = len(window_sizes)

            # データが最小ウィンドウサイズにも満たない場合の警告
            min_window_samples = int(self.config["g_quality_start"] * sampling_rate)
            if not has_inner and not has_drag:
                logger.warning(
                    "Inner Capsule/Drag Shieldのどちらのデータも存在しないため、G-quality解析をスキップします"
                )
                self.status_update.emit("データが存在しないため、G-quality解析をスキップしました")
                self.g_quality_data = []
                self.finished.emit([])
                return

            # 片側しかない場合でも、残ったセンサーで解析を続行する
            enough_data = (has_inner and data_length_inner >= min_window_samples) or (
                has_drag and data_length_drag >= min_window_samples
            )
            if not enough_data:
                logger.warning(
                    f"データ長が最小ウィンドウサイズ ({min_window_samples} samples) "
                    f"より小さいため、G-quality解析をスキップします"
                )
                self.status_update.emit("データが不十分なため、G-quality解析をスキップしました")
                self.g_quality_data = []
                self.finished.emit([])
                return

            # 全体の進捗を更新
            self.overall_progress.emit(self.file_index, self.total_files)

            # ファイル単位の処理ステータスを更新
            self.status_update.emit(f"G-quality解析中... ({self.file_index + 1}/{self.total_files})")

            for i, window_size in enumerate(window_sizes):
                # 中断フラグのチェック
                if not self.is_running:
                    break

                # ウィンドウサイズを状態更新で通知
                if i % 3 == 0:  # 3ステップごとに状態を更新（UI更新の負荷を抑制）
                    self.status_update.emit(
                        f"G-quality解析中... ウィンドウサイズ: {window_size:.2f}秒 ({self.file_index + 1}/{self.total_files})"
                    )

                # Inner CapsuleとDrag Shieldの両方について統計を計算
                min_mean_inner_capsule = None
                min_time_inner_capsule = None
                min_std_inner_capsule = None
                min_mean_drag_shield = None
                min_time_drag_shield = None
                min_std_drag_shield = None

                try:
                    if has_inner and data_length_inner >= int(window_size * sampling_rate):
                        (
                            min_mean_inner_capsule,
                            min_time_inner_capsule,
                            min_std_inner_capsule,
                        ) = calculate_statistics(
                            self.filtered_gravity_level_inner_capsule,
                            self.filtered_time,
                            {
                                "window_size": window_size,
                                "sampling_rate": self.config["sampling_rate"],
                            },
                        )
                except Exception as e:
                    log_exception(e, f"Inner Capsule: ウィンドウサイズ {window_size}秒 での統計計算中にエラー")

                try:
                    if has_drag and data_length_drag >= int(window_size * sampling_rate):
                        (
                            min_mean_drag_shield,
                            min_time_drag_shield,
                            min_std_drag_shield,
                        ) = calculate_statistics(
                            self.filtered_gravity_level_drag_shield,
                            self.filtered_adjusted_time,
                            {
                                "window_size": window_size,
                                "sampling_rate": self.config["sampling_rate"],
                            },
                        )
                except Exception as e:
                    log_exception(e, f"Drag Shield: ウィンドウサイズ {window_size}秒 での統計計算中にエラー")

                # いずれかの計算結果が有効な場合のみデータに追加
                if any(
                    value is not None
                    for value in [
                        min_mean_inner_capsule,
                        min_mean_drag_shield,
                    ]
                ):
                    g_quality_data.append(
                        (
                            window_size,
                            min_time_inner_capsule,
                            min_mean_inner_capsule,
                            min_std_inner_capsule,
                            min_time_drag_shield,
                            min_mean_drag_shield,
                            min_std_drag_shield,
                        )
                    )

                # 進捗状況を更新（0-100%）
                progress_value = int((i + 1) / total_steps * 100)
                self.progress.emit(progress_value)

            # 結果をインスタンス変数に保存（get_resultsメソッドで取得できるようにする）
            self.g_quality_data = g_quality_data

            # 有効なデータが存在しない場合の処理
            if not g_quality_data:
                logger.warning(
                    "すべてのウィンドウサイズで有効な統計が計算できませんでした。"
                    f"データ長: inner={data_length_inner}, drag={data_length_drag}"
                )
                self.status_update.emit("有効な統計データが得られませんでした")
            else:
                logger.info(f"G-quality解析完了: {len(g_quality_data)}個の有効なデータポイントを生成")
                # 状態を更新
                self.status_update.emit(f"G-quality解析が完了しました ({self.file_index + 1}/{self.total_files})")

            # 解析完了時に結果を送信（空のリストでも送信）
            self.finished.emit(g_quality_data)

        except Exception as e:
            log_exception(e, "G-quality解析中に予期せぬエラーが発生しました")
            self.status_update.emit("エラーが発生しました")
            # 例外発生時も空のリスト結果を保存
            self.g_quality_data = []
            self.finished.emit([])  # 空リストを返す

        self.status_update.emit("処理をキャンセルしました")
