#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ワーカースレッドモジュール

UIブロックを防止するためのバックグラウンド処理用のワーカースレッドを提供します。
主にG-quality解析などの時間のかかる処理を非同期で実行します。
"""

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from core.statistics import calculate_statistics


class GQualityWorker(QThread):
    """
    G-quality解析を行うワーカースレッド

    異なるウィンドウサイズでの重力レベルの標準偏差を計算し、
    最適な微小重力環境を特定するための分析を非同期で実行します。
    """

    # シグナル定義
    progress = pyqtSignal(int)  # 進捗更新用シグナル (0-100%)
    finished = pyqtSignal(list)  # 結果送信用シグナル

    def __init__(self, filtered_time, filtered_gravity_level_inner_capsule, filtered_gravity_level_drag_shield, config):
        """
        コンストラクタ

        Args:
            filtered_time (pandas.Series): フィルタリングされた時間データ
            filtered_gravity_level_inner_capsule (pandas.Series): カプセル内の重力レベルデータ
            filtered_gravity_level_drag_shield (pandas.Series): ドラッグシールドの重力レベルデータ
            config (dict): 設定情報
        """
        super().__init__()
        self.filtered_time = filtered_time
        self.filtered_gravity_level_inner_capsule = filtered_gravity_level_inner_capsule
        self.filtered_gravity_level_drag_shield = filtered_gravity_level_drag_shield
        self.config = config
        self.is_running = True

    def run(self):
        """
        スレッドの実行メソッド

        異なるウィンドウサイズでの重力レベル統計を計算し、
        結果をリストとして返します。進捗状況は進捗シグナルを通じて通知します。
        """
        g_quality_data = []
        # 設定から開始サイズ、終了サイズ、ステップサイズを取得してウィンドウサイズの配列を生成
        window_sizes = np.arange(
            self.config["g_quality_start"], self.config["g_quality_end"] + self.config["g_quality_step"], self.config["g_quality_step"]
        )
        total_steps = len(window_sizes)

        for i, window_size in enumerate(window_sizes):
            # 中断フラグのチェック
            if not self.is_running:
                break

            # Inner CapsuleとDrag Shieldの両方について統計を計算
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
            self.progress.emit(int((i + 1) / total_steps * 100))

        # 解析完了時に結果を送信
        self.finished.emit(g_quality_data)

    def stop(self):
        """
        スレッドの実行を中止する

        実行中のスレッドを安全に停止させるためのフラグを設定します。
        """
        self.is_running = False
