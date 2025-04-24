# gui/workers.py
# ワーカースレッドクラス

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from core.statistics import calculate_statistics


class GQualityWorker(QThread):
    """
    G-quality解析を行うワーカースレッドクラス
    """

    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, filtered_time, filtered_gravity_level_inner_capsule, filtered_gravity_level_drag_shield, config):
        super().__init__()
        self.filtered_time = filtered_time
        self.filtered_gravity_level_inner_capsule = filtered_gravity_level_inner_capsule
        self.filtered_gravity_level_drag_shield = filtered_gravity_level_drag_shield
        self.config = config
        self.is_running = True

    def run(self):
        g_quality_data = []
        window_sizes = np.arange(
            self.config["g_quality_start"], self.config["g_quality_end"] + self.config["g_quality_step"], self.config["g_quality_step"]
        )
        total_steps = len(window_sizes)

        for i, window_size in enumerate(window_sizes):
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

            # 進捗状況を更新
            self.progress.emit(int((i + 1) / total_steps * 100))

        # 解析完了時に結果を送信
        self.finished.emit(g_quality_data)

    def stop(self):
        self.is_running = False
