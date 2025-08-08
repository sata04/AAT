#!/usr/bin/env python3
"""
統計計算モジュール

重力レベルデータの統計分析のための機能を提供します。
特定のウィンドウサイズにおける標準偏差が最小となる区間を検出し、
その区間の平均重力レベルや開始時間を計算します。
また、ユーザーが選択した特定範囲の統計情報も計算します。
"""

from typing import Optional, Union

import numpy as np
import pandas as pd


def calculate_statistics(
    gravity_level: pd.Series, time: pd.Series, config: dict[str, Union[float, int]]
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    重力レベルデータの統計情報を計算する

    指定されたウィンドウサイズで重力レベルデータをスキャンし、
    標準偏差が最小となる時間窓を特定します。その窓内の絶対値の平均値、
    開始時間、および標準偏差を返します。

    Args:
        gravity_level: 重力レベルデータ
        time: 時間データ
        config: 設定パラメータ辞書。以下のキーが使用されます：
            - window_size (float): 解析窓のサイズ（秒単位）、デフォルトは0.1
            - sampling_rate (int): サンプリングレート（Hz単位）、デフォルトは1000

    Returns:
        以下の3つの値を含むタプル
            - 最小標準偏差ウィンドウの絶対値の平均値
            - 最小標準偏差ウィンドウの開始時間
            - 最小標準偏差値
            データが不十分な場合はすべてNone
    """
    window_size: float = float(config.get("window_size", 0.1))
    sampling_rate: int = int(config.get("sampling_rate", 1000))
    window_size_samples: int = int(window_size * sampling_rate)

    std_devs: Union[list[float], np.ndarray] = []
    means: Union[list[float], np.ndarray] = []
    times: Union[list[float], np.ndarray] = []

    # データ長の一致を確認
    if len(gravity_level) != len(time):
        raise ValueError(
            f"時間配列とデータ配列の長さが一致しません: gravity_level={len(gravity_level)}, time={len(time)}"
        )

    # データがウィンドウサイズに満たない場合
    if len(gravity_level) < window_size_samples:
        return None, None, None

    # numpy配列に変換してパフォーマンスを向上
    gravity_array: np.ndarray = np.asarray(gravity_level.values)
    time_array: np.ndarray = np.asarray(time.values)

    # 事前割り当てでメモリ効率を改善
    num_windows = len(gravity_level) - window_size_samples + 1
    std_devs = np.empty(num_windows)
    means = np.empty(num_windows)
    times = np.empty(num_windows)

    # スライディングウィンドウで計算（numpy配列で高速化）
    for i in range(num_windows):
        window = gravity_array[i : i + window_size_samples]
        std_devs[i] = float(np.std(window))
        means[i] = float(np.mean(np.abs(window)))  # 絶対値の平均を計算
        times[i] = time_array[i]

    if len(std_devs) == 0:
        return None, None, None

    # 最小標準偏差のインデックスを見つける
    min_std_index: int = int(np.argmin(std_devs))
    return float(means[min_std_index]), float(times[min_std_index]), float(std_devs[min_std_index])


def calculate_range_statistics(data_array: np.ndarray) -> dict[str, Optional[float]]:
    """
    選択された範囲のデータに対して統計情報を計算する

    Args:
        data_array: 統計情報を計算するデータ配列

    Returns:
        以下の統計情報を含む辞書
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
        "mean": float(np.mean(data_array)),
        "abs_mean": float(np.mean(np.abs(data_array))),
        "std": float(np.std(data_array)),
        "min": float(np.min(data_array)),
        "max": float(np.max(data_array)),
        "range": float(np.max(data_array) - np.min(data_array)),
        "count": len(data_array),
    }
