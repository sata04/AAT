#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ワーカースレッドモジュール

UIブロックを防止するためのバックグラウンド処理用のワーカースレッドを提供します。
主にG-quality解析などの時間のかかる処理を非同期で実行します。
"""

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

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
    progress = pyqtSignal(int)  # 進捗更新用シグナル (0-100%)
    status_update = pyqtSignal(str)  # 状態更新用シグナル
    overall_progress = pyqtSignal(int, int)  # 全体の進捗用シグナル (現在のファイル, 総ファイル数)
    finished = pyqtSignal(list)  # 結果送信用シグナル

    def __init__(self, filtered_time, filtered_gravity_level_inner_capsule, filtered_gravity_level_drag_shield, config, file_index=0, total_files=1):
        """
        コンストラクタ

        Args:
            filtered_time (pandas.Series): フィルタリングされた時間データ
            filtered_gravity_level_inner_capsule (pandas.Series): カプセル内の重力レベルデータ
            filtered_gravity_level_drag_shield (pandas.Series): ドラッグシールドの重力レベルデータ
            config (dict): 設定情報
            file_index (int, optional): 現在処理中のファイルのインデックス。デフォルトは0。
            total_files (int, optional): 処理する総ファイル数。デフォルトは1。
        """
        super().__init__()
        self.filtered_time = filtered_time
        self.filtered_gravity_level_inner_capsule = filtered_gravity_level_inner_capsule
        self.filtered_gravity_level_drag_shield = filtered_gravity_level_drag_shield
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
        return self.g_quality_data

    def run(self):
        """
        スレッドの実行メソッド

        異なるウィンドウサイズでの重力レベル統計を計算し、
        結果をリストとして返します。進捗状況は進捗シグナルを通じて通知します。
        """
        try:
            g_quality_data = []
            # 設定から開始サイズ、終了サイズ、ステップサイズを取得してウィンドウサイズの配列を生成
            window_sizes = np.arange(
                self.config["g_quality_start"], self.config["g_quality_end"] + self.config["g_quality_step"], self.config["g_quality_step"]
            )
            total_steps = len(window_sizes)

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
                    self.status_update.emit(f"G-quality解析中... ウィンドウサイズ: {window_size:.2f}秒 ({self.file_index + 1}/{self.total_files})")

                # Inner CapsuleとDrag Shieldの両方について統計を計算
                try:
                    min_mean_inner_capsule, min_time_inner_capsule, min_std_inner_capsule = calculate_statistics(
                        self.filtered_gravity_level_inner_capsule,
                        self.filtered_time,
                        {"window_size": window_size, "sampling_rate": self.config["sampling_rate"]},
                    )
                    min_mean_drag_shield, min_time_drag_shield, min_std_drag_shield = calculate_statistics(
                        self.filtered_gravity_level_drag_shield,
                        self.filtered_time,
                        {"window_size": window_size, "sampling_rate": self.config["sampling_rate"]},
                    )
                except Exception as e:
                    log_exception(e, f"ウィンドウサイズ {window_size}秒 での統計計算中にエラー")
                    continue

                # 計算結果が有効な場合のみデータに追加
                if (
                    min_mean_inner_capsule is not None
                    and min_time_inner_capsule is not None
                    and min_std_inner_capsule is not None
                    and min_mean_drag_shield is not None
                    and min_time_drag_shield is not None
                    and min_std_drag_shield is not None
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

            # 状態を更新
            self.status_update.emit(f"G-quality解析が完了しました ({self.file_index + 1}/{self.total_files})")

            # 解析完了時に結果を送信
            self.finished.emit(g_quality_data)

        except Exception as e:
            log_exception(e, "G-quality解析中に予期せぬエラーが発生しました")
            self.status_update.emit("エラーが発生しました")
            # 例外発生時も空のリスト結果を保存
            self.g_quality_data = []
            self.finished.emit([])  # 空リストを返す

    def stop(self):
        """
        スレッドの実行を中止する

        実行中のスレッドを安全に停止させるためのフラグを設定します。
        """
        self.is_running = False
        self.status_update.emit("処理をキャンセルしました")
