#!/usr/bin/env python3
"""
統計計算モジュール

重力レベルデータの統計分析のための機能を提供します。
特定のウィンドウサイズにおける標準偏差が最小となる区間を検出し、
その区間の平均重力レベルや開始時間を計算します。
また、ユーザーが選択した特定範囲の統計情報も計算します。
"""

import numpy as np


def calculate_statistics(gravity_level, time, config):
    """
    重力レベルデータの統計情報を計算する

    指定されたウィンドウサイズで重力レベルデータをスキャンし、
    標準偏差が最小となる時間窓を特定します。その窓内の絶対値の平均値、
    開始時間、および標準偏差を返します。

    Args:
        gravity_level (pandas.Series): 重力レベルデータ
        time (pandas.Series): 時間データ
        config (dict): 設定パラメータ辞書。以下のキーが使用されます：
            - window_size (float): 解析窓のサイズ（秒単位）、デフォルトは0.1
            - sampling_rate (int): サンプリングレート（Hz単位）、デフォルトは1000

    Returns:
        tuple: 以下の3つの値を含むタプル
            - float or None: 最小標準偏差ウィンドウの絶対値の平均値
            - float or None: 最小標準偏差ウィンドウの開始時間
            - float or None: 最小標準偏差値
            データが不十分な場合はすべてNone
    """
    window_size = config.get("window_size", 0.1)
    sampling_rate = config.get("sampling_rate", 1000)
    window_size_samples = int(window_size * sampling_rate)
    std_devs = []
    means = []
    times = []

    # データがウィンドウサイズに満たない場合
    if len(gravity_level) < window_size_samples:
        return None, None, None

    # スライディングウィンドウで計算
    for i in range(len(gravity_level) - window_size_samples + 1):
        window = gravity_level[i : i + window_size_samples]
        std_devs.append(np.std(window))
        means.append(np.mean(np.abs(window)))  # 絶対値の平均を計算
        times.append(time.iloc[i])

    if not std_devs:
        return None, None, None

    # 最小標準偏差のインデックスを見つける
    min_std_index = np.argmin(std_devs)
    return means[min_std_index], times[min_std_index], std_devs[min_std_index]


def calculate_range_statistics(data_array):
    """
    選択された範囲のデータに対して統計情報を計算する

    Args:
        data_array (numpy.array): 統計情報を計算するデータ配列

    Returns:
        dict: 以下の統計情報を含む辞書
            - mean: 平均値
            - abs_mean: 絶対値の平均
            - std: 標準偏差
            - min: 最小値
            - max: 最大値
            - range: 最大値と最小値の差
            - count: データポイント数
    """
    if len(data_array) == 0:
        return {
            "mean": None,
            "abs_mean": None,
            "std": None,
            "min": None,
            "max": None,
            "range": None,
            "count": 0,
        }

    return {
        "mean": np.mean(data_array),
        "abs_mean": np.mean(np.abs(data_array)),
        "std": np.std(data_array),
        "min": np.min(data_array),
        "max": np.max(data_array),
        "range": np.max(data_array) - np.min(data_array),
        "count": len(data_array),
    }
