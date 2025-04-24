# core/statistics.py
# 統計計算機能

import numpy as np


def calculate_statistics(gravity_level, time, config):
    """
    重力レベルデータの統計情報を計算する

    Parameters:
    gravity_level (pandas.Series): 重力レベルデータ
    time (pandas.Series): 時間データ
    config (dict): 設定情報

    Returns:
    tuple: (最小標準偏差ウィンドウの平均値, 最小標準偏差ウィンドウの開始時間, 最小標準偏差値)
    """
    window_size = config.get("window_size", 0.1)
    sampling_rate = config.get("sampling_rate", 1000)
    window_size_samples = int(window_size * sampling_rate)
    std_devs = []
    means = []
    times = []

    if len(gravity_level) < window_size_samples:
        print(f"警告: データ点数 ({len(gravity_level)}) がウィンドウサイズ ({window_size_samples}) より小さいです。")
        return None, None, None

    # 絶対値を使用して平均を計算
    for i in range(len(gravity_level) - window_size_samples + 1):
        window = gravity_level[i : i + window_size_samples]
        std_devs.append(np.std(window))
        means.append(np.mean(np.abs(window)))  # 絶対値の平均を計算
        times.append(time.iloc[i])

    if not std_devs:
        print("警告: 標準偏差の計算結果が空です。")
        return None, None, None

    min_std_index = np.argmin(std_devs)
    return means[min_std_index], times[min_std_index], std_devs[min_std_index]
