#!/usr/bin/env python3
"""
統計計算モジュール

重力レベルデータの統計分析のための機能を提供します。
特定のウィンドウサイズにおける標準偏差が最小となる区間を検出し、
その区間の平均重力レベルや開始時間を計算します。
また、ユーザーが選択した特定範囲の統計情報も計算します。
"""

import numpy as np
import pandas as pd


def calculate_statistics(
    gravity_level: pd.Series, time: pd.Series, config: dict[str, float | int]
) -> tuple[float | None, float | None, float | None]:
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
    window_size_samples: int = max(1, round(window_size * sampling_rate))

    # データ長の一致を確認
    if len(gravity_level) != len(time):
        raise ValueError(
            f"時間配列とデータ配列の長さが一致しません: gravity_level={len(gravity_level)}, time={len(time)}"
        )

    # データがウィンドウサイズに満たない場合
    if len(gravity_level) < window_size_samples:
        return None, None, None

    # numpy配列に変換
    gravity_array: np.ndarray = np.asarray(gravity_level.values, dtype=np.float64)
    time_array: np.ndarray = np.asarray(time.values, dtype=np.float64)

    num_windows = len(gravity_array) - window_size_samples + 1

    # NaN対応のベクトル化ローリング計算 O(n)
    # NaNを0に置換し、有効値のカウントを別途追跡する
    valid_mask = ~np.isnan(gravity_array)
    safe_vals = np.where(valid_mask, gravity_array, 0.0)
    abs_vals = np.where(valid_mask, np.abs(gravity_array), 0.0)
    sq_vals = np.where(valid_mask, gravity_array**2, 0.0)
    valid_f = valid_mask.astype(np.float64)

    # 累積和によるローリングウィンドウ集計（O(n)）
    def _rolling_sum(arr: np.ndarray, w: int) -> np.ndarray:
        cs = np.empty(len(arr) + 1, dtype=np.float64)
        cs[0] = 0.0
        np.cumsum(arr, out=cs[1:])
        return cs[w:] - cs[:-w]

    w = window_size_samples
    count = _rolling_sum(valid_f, w)  # 各ウィンドウの有効値数
    sum_x = _rolling_sum(safe_vals, w)  # Σx
    sum_x2 = _rolling_sum(sq_vals, w)  # Σx²
    sum_abs = _rolling_sum(abs_vals, w)  # Σ|x|

    # ウィンドウ内に有効値がない場合はNaN
    with np.errstate(invalid="ignore", divide="ignore"):
        rolling_mean = np.where(count > 0, sum_x / count, np.nan)
        rolling_mean_sq = np.where(count > 0, sum_x2 / count, np.nan)
        means = np.where(count > 0, sum_abs / count, np.nan)
        # var = E[X²] - E[X]², 数値誤差で微小な負値になり得るので0にクランプ
        variance = np.maximum(rolling_mean_sq - rolling_mean**2, 0.0)
        std_devs = np.sqrt(variance)
        # 有効値0のウィンドウはNaN
        std_devs = np.where(count > 0, std_devs, np.nan)

    times = time_array[:num_windows]

    if num_windows == 0 or np.all(np.isnan(std_devs)):
        return None, None, None

    if np.all(np.isnan(means)):
        return None, None, None

    # 最小標準偏差のインデックスを見つける（NaNを無視）
    min_std_index: int = int(np.nanargmin(std_devs))
    return float(means[min_std_index]), float(times[min_std_index]), float(std_devs[min_std_index])


def calculate_range_statistics(data_array: np.ndarray) -> dict[str, float | None]:
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
