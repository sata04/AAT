#!/usr/bin/env python3
"""
データ処理モジュール

CSVファイルからのデータ読み込み、列の自動検出、重力レベルの計算、
およびデータのフィルタリング機能を提供します。
"""

from typing import Any

import numpy as np
import pandas as pd

from core.exceptions import ColumnNotFoundError, DataLoadError, DataProcessingError, SyncPointNotFoundError
from core.logger import get_logger, log_exception

# モジュール用のロガーを初期化
logger = get_logger("data_processor")


def detect_columns(file_path: str) -> tuple[list[str], list[str]]:
    """
    CSVファイルから時間列と加速度列の候補を検出する

    カラム名に基づいて時間データと加速度データの候補となる列を特定します。
    カラム名に明示的な情報がない場合は数値データ型の列を候補とします。

    Args:
        file_path (str): CSVファイルのパス

    Returns:
        tuple: 以下の2つのリストを含むタプル
            - list: 時間列の候補リスト
            - list: 加速度列の候補リスト

    Raises:
        ValueError: 列検出中にエラーが発生した場合
    """
    try:
        data = pd.read_csv(file_path)
        logger.debug(f"読み込んだCSVのカラム: {data.columns.tolist()}")

        time_columns: list[str] = []
        acceleration_columns: list[str] = []

        # カラム名に基づいて候補を検出
        for column in data.columns:
            col_lower = column.lower()

            # 時間列の候補を検出
            if any(keyword in col_lower for keyword in ["time", "時間", "秒", "s", "sec", "t"]):
                time_columns.append(column)

            # 加速度列の候補を検出
            if any(keyword in col_lower for keyword in ["acc", "加速度", "a", "accel", "acceleration", "g"]):
                acceleration_columns.append(column)

        # 名前ベースの検出で候補がない場合は、数値データ型のカラムを候補に追加
        if not time_columns:
            for column in data.columns:
                if pd.api.types.is_numeric_dtype(data[column]) and column not in acceleration_columns:
                    time_columns.append(column)

        if not acceleration_columns:
            # 時間列の候補を除外して、残りの数値カラムを加速度列の候補とする
            for column in data.columns:
                if pd.api.types.is_numeric_dtype(data[column]) and column not in time_columns:
                    acceleration_columns.append(column)

        logger.debug(f"検出された時間列候補: {time_columns}")
        logger.debug(f"検出された加速度列候補: {acceleration_columns}")

        return time_columns, acceleration_columns

    except Exception as e:
        log_exception(e, "列候補の検出中にエラーが発生しました")
        raise DataLoadError(file_path, "列候補の検出に失敗しました", e) from e


def load_and_process_data(file_path: str, config: dict[str, Any]) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    CSVファイルからデータを読み込み、処理する

    CSVファイルから時間と加速度のデータを読み込み、重力レベルに変換します。
    また、Drag Shieldの同期点を検出し、時間を調整します。

    Args:
        file_path (str): CSVファイルのパス
        config (dict): 設定情報

    Returns:
        tuple: 以下の4つの要素を含むタプル
            - pandas.Series: Inner Capsuleの調整済み時間データ
            - pandas.Series: Inner Capsuleの重力レベル
            - pandas.Series: Drag Shieldの重力レベル
            - pandas.Series: Drag Shieldの調整済み時間データ

    Raises:
        ValueError: データ読み込み中にエラーが発生した場合
    """
    logger.info(f"ファイルからデータを読み込み: {file_path}")
    try:
        data = pd.read_csv(file_path)
        logger.debug(f"読み込んだCSVのカラム: {data.columns.tolist()}")

        # 設定から列名を取得
        time_column = config["time_column"]
        acceleration_inner_column = config["acceleration_column_inner_capsule"]
        acceleration_drag_column = config["acceleration_column_drag_shield"]

        # 列が存在するか確認
        columns_exist = all(
            col in data.columns
            for col in [
                time_column,
                acceleration_inner_column,
                acceleration_drag_column,
            ]
        )

        if not columns_exist:
            # この場合は呼び出し元で列の選択ダイアログを表示するためにエラーを送出
            missing_columns = []
            for col in [time_column, acceleration_inner_column, acceleration_drag_column]:
                if col not in data.columns:
                    missing_columns.append(col)
            raise ColumnNotFoundError(file_path, missing_columns, data.columns.tolist())

        time = data[time_column]
        acceleration_inner_capsule = data[acceleration_inner_column]
        acceleration_drag_shield = data[acceleration_drag_column]

        # Inner加速度計の上下反転補正
        if config.get("invert_inner_acceleration", False):
            logger.info("Inner加速度計の上下反転補正を適用します")
            acceleration_inner_capsule = -acceleration_inner_capsule

        # 加速度の閾値（デフォルト1m/s^2）を設定
        acceleration_threshold = config.get("acceleration_threshold", 1.0)
        logger.debug(f"加速度閾値: {acceleration_threshold}")

        # Drag ShieldとInner Capsuleの同期点を見つける
        sync_indices_drag = np.where(np.abs(acceleration_drag_shield) < acceleration_threshold)[0]
        sync_indices_inner = np.where(np.abs(acceleration_inner_capsule) < acceleration_threshold)[0]
        logger.debug(
            f"Drag Shield同期点候補数: {len(sync_indices_drag)}, Inner Capsule同期点候補数: {len(sync_indices_inner)}"
        )

        if len(sync_indices_drag) > 0:
            sync_index_drag = sync_indices_drag[0]
            # Inner側の同期点はInner Capsuleに存在すればそれを、なければDrag Shieldと同じ位置を使用
            sync_index_inner = sync_indices_inner[0] if len(sync_indices_inner) > 0 else sync_index_drag
        else:
            logger.error("Drag Shieldの同期点が見つかりませんでした")
            raise SyncPointNotFoundError("Drag Shield")

        logger.info(f"同期点を検出: inner_index={sync_index_inner}, drag_index={sync_index_drag}")

        # 各系列の時間を同期点基準で調整
        adjusted_time_inner = pd.Series(time - time.iloc[sync_index_inner])
        adjusted_time_drag = pd.Series(time - time.iloc[sync_index_drag])

        gravity_level_inner_capsule = acceleration_inner_capsule / config["gravity_constant"]
        gravity_level_drag_shield = acceleration_drag_shield / config["gravity_constant"]

        # 処理結果のサンプル値をログに記録
        logger.debug(
            f"重力レベル計算 (先頭5件): inner_capsule={gravity_level_inner_capsule.head(5).tolist()}, "
            f"drag_shield={gravity_level_drag_shield.head(5).tolist()}"
        )

        # 調整済み時間を返却（inner, drag）
        return (
            adjusted_time_inner,
            gravity_level_inner_capsule,
            gravity_level_drag_shield,
            adjusted_time_drag,
        )
    except (ColumnNotFoundError, SyncPointNotFoundError):
        # カスタム例外はそのまま再送出
        raise
    except Exception as e:
        log_exception(e, "データの読み込み中にエラーが発生しました")
        raise DataLoadError(file_path, "データの読み込みに失敗しました", e) from e


def _find_start_indices(time: pd.Series, adjusted_time: pd.Series) -> tuple[int, int]:
    """
    時間データから開始インデックスを検出する

    Args:
        time: Inner Capsuleの時間データ
        adjusted_time: Drag Shieldの調整済み時間データ

    Returns:
        Inner CapsuleとDrag Shieldの開始インデックス
    """
    # 開始点は0秒から - インデックスエラーを防止するためのチェックを追加
    start_indices_inner = np.where(time >= 0)[0]
    if len(start_indices_inner) > 0:
        start_index_inner = start_indices_inner[0]
    else:
        logger.warning("Inner capsuleの開始点が見つかりませんでした。最初のインデックスを使用します。")
        start_index_inner = 0

    start_indices_drag = np.where(adjusted_time >= 0)[0]
    if len(start_indices_drag) > 0:
        start_index_drag = start_indices_drag[0]
    else:
        logger.warning("Drag shieldの開始点が見つかりませんでした。最初のインデックスを使用します。")
        start_index_drag = 0

    return start_index_inner, start_index_drag


def _find_end_indices(
    gravity_level_inner_capsule: pd.Series,
    gravity_level_drag_shield: pd.Series,
    min_index_inner: int,
    min_index_drag: int,
    end_gravity_level: float,
) -> tuple[int, int]:
    """
    終了重力レベルに基づいて終了インデックスを検出する

    Args:
        gravity_level_inner_capsule: Inner Capsuleの重力レベル
        gravity_level_drag_shield: Drag Shieldの重力レベル
        min_index_inner: Inner Capsuleの最小インデックス
        min_index_drag: Drag Shieldの最小インデックス
        end_gravity_level: 終了重力レベル闾値

    Returns:
        Inner CapsuleとDrag Shieldの終了インデックス
    """
    # 最小インデックス以降で終了インデックスを計算
    end_index_inner_candidates = np.where(gravity_level_inner_capsule >= end_gravity_level)[0]
    end_index_inner = np.array([i for i in end_index_inner_candidates if i >= min_index_inner])

    end_index_drag_candidates = np.where(gravity_level_drag_shield >= end_gravity_level)[0]
    end_index_drag = np.array([i for i in end_index_drag_candidates if i >= min_index_drag])

    # データセットごとに個別の終了点を設定
    if len(end_index_inner) > 0:
        end_index_inner = end_index_inner[0]
        logger.debug(f"Inner capsuleの終了インデックス: {end_index_inner}")
    else:
        end_index_inner = len(gravity_level_inner_capsule) - 1
        logger.warning(f"Inner capsuleの終了点が見つからず、データの最後を使用: {end_index_inner}")

    if len(end_index_drag) > 0:
        end_index_drag = end_index_drag[0]
        logger.debug(f"Drag shieldの終了インデックス: {end_index_drag}")
    else:
        end_index_drag = len(gravity_level_drag_shield) - 1
        logger.warning(f"Drag shieldの終了点が見つからず、データの最後を使用: {end_index_drag}")

    return end_index_inner, end_index_drag


def filter_data(
    time: pd.Series,
    gravity_level_inner_capsule: pd.Series,
    gravity_level_drag_shield: pd.Series,
    adjusted_time: pd.Series,
    config: dict[str, Any],
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, int]:
    """
    データをフィルタリングする

    時間=0を基準にデータをトリミングし、終了重力レベル（end_gravity_level）
    に達するまでのデータを抽出します。Inner CapsuleとDrag Shieldのデータは
    独立してフィルタリングされます。

    Args:
        time (pandas.Series): 時間データ
        gravity_level_inner_capsule (pandas.Series): Inner Capsuleの重力レベル
        gravity_level_drag_shield (pandas.Series): Drag Shieldの重力レベル
        adjusted_time (pandas.Series): 調整された時間データ
        config (dict): 設定情報

    Returns:
        tuple: 以下の5つの要素を含むタプル
            - pandas.Series: フィルタリングされた時間データ
            - pandas.Series: フィルタリングされたInner Capsuleの重力レベル
            - pandas.Series: フィルタリングされたDrag Shieldの重力レベル
            - pandas.Series: フィルタリングされた調整時間データ
            - int: 終了インデックス
    """
    logger.info("データのフィルタリングを開始")

    # データ長をログに記録
    logger.info(
        f"データサイズ: inner_capsule={len(gravity_level_inner_capsule)}, "
        f"drag_shield={len(gravity_level_drag_shield)}, "
        f"time={len(time)}, adjusted_time={len(adjusted_time)}"
    )

    # データが不足している場合の警告
    min_data_length = min(len(gravity_level_inner_capsule), len(gravity_level_drag_shield))
    if min_data_length < config.get("sampling_rate", 1000) * config.get("window_size", 0.1):
        logger.warning(
            f"データ長が不足しています。最小データ長: {min_data_length}, "
            f"必要な最小長: {config.get('sampling_rate', 1000) * config.get('window_size', 0.1)}"
        )

    try:
        # 開始インデックスを検出
        start_index_inner, start_index_drag = _find_start_indices(time, adjusted_time)
        logger.debug(f"開始インデックス: inner={start_index_inner}, drag={start_index_drag}")

        # 開始点からの最小秒数を取得
        min_seconds_after_start = config.get("min_seconds_after_start", 0.0)
        logger.debug(f"開始点からの最小秒数: {min_seconds_after_start}")

        # Inner capsuleのデータで、開始点からmin_seconds_after_start秒後以降のインデックスを計算
        # インデックスエラーを防止するためのチェックを追加
        min_time_inner = time.iloc[start_index_inner] + min_seconds_after_start
        min_indices_inner = np.where(time >= min_time_inner)[0]
        if len(min_indices_inner) > 0:
            min_index_inner = min_indices_inner[0]
        else:
            logger.warning("Inner capsuleの最小時間点が見つかりませんでした。開始インデックスを使用します。")
            min_index_inner = start_index_inner

        logger.debug(f"Inner capsuleの最小時間インデックス: {min_index_inner}, 時間: {time.iloc[min_index_inner]}")

        # Drag shieldのデータで、開始点からmin_seconds_after_start秒後以降のインデックスを計算
        # インデックスエラーを防止するためのチェックを追加
        min_time_drag = adjusted_time.iloc[start_index_drag] + min_seconds_after_start
        min_indices_drag = np.where(adjusted_time >= min_time_drag)[0]
        if len(min_indices_drag) > 0:
            min_index_drag = min_indices_drag[0]
        else:
            logger.warning("Drag shieldの最小時間点が見つかりませんでした。開始インデックスを使用します。")
            min_index_drag = start_index_drag

        logger.debug(f"Drag shieldの最小時間インデックス: {min_index_drag}, 時間: {adjusted_time.iloc[min_index_drag]}")

        # 終了インデックスを検出
        end_index_inner, end_index_drag = _find_end_indices(
            gravity_level_inner_capsule,
            gravity_level_drag_shield,
            min_index_inner,
            min_index_drag,
            config["end_gravity_level"],
        )

        # データセットごとに個別にフィルタリング
        filtered_time = time[start_index_inner : end_index_inner + 1]
        filtered_gravity_level_inner_capsule = gravity_level_inner_capsule[start_index_inner : end_index_inner + 1]

        filtered_adjusted_time = adjusted_time[start_index_drag : end_index_drag + 1]
        filtered_gravity_level_drag_shield = gravity_level_drag_shield[start_index_drag : end_index_drag + 1]

        # データサイズをログに記録
        logger.debug(
            f"フィルタリング結果のサイズ: inner={len(filtered_gravity_level_inner_capsule)}, "
            f"drag={len(filtered_gravity_level_drag_shield)}"
        )

        # 統計情報の計算のために全体の終了インデックスを保持
        end_index = max(end_index_inner, end_index_drag)

        return (
            filtered_time,
            filtered_gravity_level_inner_capsule,
            filtered_gravity_level_drag_shield,
            filtered_adjusted_time,
            end_index,
        )

    except Exception as e:
        log_exception(e, "フィルタリング中にエラーが発生しました")

        # データ長の違いに起因するエラーの場合、より詳細な情報を提供
        if "index" in str(e).lower() or "length" in str(e).lower():
            min_length = min(
                len(time), len(adjusted_time), len(gravity_level_inner_capsule), len(gravity_level_drag_shield)
            )
            details = (
                f"inner_capsule: {len(gravity_level_inner_capsule)}, "
                f"drag_shield: {len(gravity_level_drag_shield)}, "
                f"min_length: {min_length}"
            )
            raise DataProcessingError("データ長の不一致によりフィルタリングに失敗しました", details) from e

        raise DataProcessingError("フィルタリング中に予期しないエラーが発生しました") from e
