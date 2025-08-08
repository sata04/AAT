#!/usr/bin/env python3
"""
キャッシュ管理モジュール

処理されたデータのキャッシュを管理します。
同じ設定・同じバージョンのアプリケーションで処理済みのファイルを
再利用できるようにします。
"""

import hashlib
import json
import os
import pickle
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.config import APP_VERSION
from core.logger import get_logger, log_exception

# ロガーの初期化
logger = get_logger("cache_manager")


def generate_cache_id(file_path, config):
    """
    CSVファイルと設定に基づいてキャッシュIDを生成する

    Args:
        file_path (str): 元のCSVファイルのパス
        config (dict): 現在の設定情報

    Returns:
        str: 一意のキャッシュID
    """
    # ファイルの最終更新時間を取得
    file_mtime = os.path.getmtime(file_path)

    # キャッシュIDに影響する設定キーを抽出
    cache_relevant_keys = [
        "time_column",
        "acceleration_column_inner_capsule",
        "acceleration_column_drag_shield",
        "sampling_rate",
        "gravity_constant",
        "acceleration_threshold",
        "end_gravity_level",
        "min_seconds_after_start",
        "app_version",
    ]

    # 設定情報のサブセットを作成
    config_subset = {key: config.get(key) for key in cache_relevant_keys}

    # ファイルパス、最終更新時間、設定情報を結合
    cache_data = f"{file_path}:{file_mtime}:{json.dumps(config_subset, sort_keys=True)}"

    # SHA-256ハッシュを計算
    cache_id = hashlib.sha256(cache_data.encode()).hexdigest()

    logger.debug(f"ファイル {os.path.basename(file_path)} のキャッシュID: {cache_id}")
    return cache_id


def get_cache_path(file_path, cache_id):
    """
    キャッシュファイルのパスを生成する

    Args:
        file_path (str): 元のCSVファイルのパス
        cache_id (str): キャッシュID

    Returns:
        str: キャッシュファイルのパス
    """
    # CSVファイルのディレクトリを取得
    csv_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    # キャッシュディレクトリのパスを生成
    cache_dir = os.path.join(csv_dir, "results_AAT", "cache")
    os.makedirs(cache_dir, exist_ok=True)

    # キャッシュファイルのパスを生成
    cache_file = f"{base_name}_{cache_id}.pickle"
    cache_path = os.path.join(cache_dir, cache_file)

    return cache_path


def save_to_cache(processed_data, file_path, cache_id, config):
    """
    処理済みデータをキャッシュとして保存する

    Args:
        processed_data (dict): 処理済みのデータ
        file_path (str): 元のCSVファイルのパス
        cache_id (str): キャッシュID
        config (dict): 現在の設定情報

    Returns:
        bool: 保存に成功した場合はTrue、失敗した場合はFalse
    """
    try:
        cache_path = get_cache_path(file_path, cache_id)

        # キャッシュメタデータを準備
        cache_metadata = {
            "created_at": datetime.now().isoformat(),
            "file_path": file_path,
            "file_mtime": os.path.getmtime(file_path),
            "app_version": APP_VERSION,
            "config": {
                key: config.get(key)
                for key in [
                    "time_column",
                    "acceleration_column_inner_capsule",
                    "acceleration_column_drag_shield",
                    "sampling_rate",
                    "gravity_constant",
                    "acceleration_threshold",
                    "end_gravity_level",
                    "min_seconds_after_start",
                ]
            },
        }

        # 保存する前に大きなデータをコピー
        data_to_save = processed_data.copy()

        # Pandasオブジェクトが安全に保存されているか確認
        if "raw_data" in data_to_save:
            # rawデータはサイズが大きいため、サイズ削減のためにhdfで保存
            cache_path_obj = Path(cache_path)
            raw_data_cache_path = cache_path_obj.with_name(cache_path_obj.stem + "_raw.h5")
            data_to_save["raw_data"].to_hdf(raw_data_cache_path, key="raw_data", mode="w")
            data_to_save["raw_data"] = None  # pickleには保存しないよう置き換え

        # メタデータを追加
        data_to_save["_metadata"] = cache_metadata

        # キャッシュに保存
        with open(cache_path, "wb") as f:
            pickle.dump(data_to_save, f)

        logger.info(f"データをキャッシュに保存しました: {cache_path}")
        return True

    except Exception as e:
        log_exception(e, "キャッシュへの保存中にエラーが発生しました")
        return False


def load_from_cache(file_path, cache_id):
    """
    キャッシュからデータを読み込む

    Args:
        file_path (str): 元のCSVファイルのパス
        cache_id (str): キャッシュID

    Returns:
        dict or None: 処理済みのデータ、またはキャッシュが存在しない場合はNone
    """
    try:
        cache_path = get_cache_path(file_path, cache_id)

        # キャッシュファイルが存在するか確認
        if not os.path.exists(cache_path):
            logger.debug(f"キャッシュファイルが見つかりません: {cache_path}")
            return None

        # キャッシュからデータを読み込み
        with open(cache_path, "rb") as f:
            data = pickle.load(f)

        # メタデータを確認
        metadata = data.get("_metadata", {})
        if metadata.get("app_version") != APP_VERSION:
            logger.warning(
                f"キャッシュのバージョン({metadata.get('app_version')})が現在のバージョン({APP_VERSION})と一致しません"
            )
            return None

        logger.info(f"キャッシュからデータを読み込みました: {cache_path}")

        # raw_dataがあれば復元
        if "raw_data" in data and data["raw_data"] is None:
            cache_path_obj = Path(cache_path)
            raw_data_cache_path = cache_path_obj.with_name(cache_path_obj.stem + "_raw.h5")
            if os.path.exists(raw_data_cache_path):
                try:
                    data["raw_data"] = pd.read_hdf(raw_data_cache_path, key="raw_data")
                    logger.debug(f"raw_dataを復元しました: {raw_data_cache_path}")
                except Exception as e:
                    log_exception(e, "raw_dataの復元中にエラーが発生しました")
                    # raw_dataの読み込みに失敗しても、他のデータは返す

        # メタデータを削除してデータを返す
        if "_metadata" in data:
            del data["_metadata"]

        return data

    except Exception as e:
        log_exception(e, "キャッシュからの読み込み中にエラーが発生しました")
        return None


def delete_cache(file_path, cache_id=None):
    """
    キャッシュを削除する

    Args:
        file_path (str): 元のCSVファイルのパス
        cache_id (str, optional): 削除するキャッシュのID。指定しない場合は全てのキャッシュを削除

    Returns:
        bool: 削除に成功した場合はTrue、失敗した場合はFalse
    """
    try:
        csv_dir = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        cache_dir = os.path.join(csv_dir, "results_AAT", "cache")

        # キャッシュディレクトリが存在するか確認
        if not os.path.exists(cache_dir):
            logger.debug(f"キャッシュディレクトリが見つかりません: {cache_dir}")
            return False

        if cache_id:
            # 特定のキャッシュだけを削除
            cache_path = get_cache_path(file_path, cache_id)
            cache_path_obj = Path(cache_path)
            raw_data_cache_path = cache_path_obj.with_name(cache_path_obj.stem + "_raw.h5")

            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"キャッシュを削除しました: {cache_path}")

            if os.path.exists(raw_data_cache_path):
                os.remove(raw_data_cache_path)
                logger.info(f"raw_dataキャッシュを削除しました: {raw_data_cache_path}")
        else:
            # このファイルの全てのキャッシュを削除
            cache_pattern = f"{base_name}_"
            for filename in os.listdir(cache_dir):
                if filename.startswith(cache_pattern) and filename.endswith((".pickle", "_raw.h5")):
                    file_path = os.path.join(cache_dir, filename)
                    os.remove(file_path)
                    logger.info(f"キャッシュを削除しました: {file_path}")

        return True

    except Exception as e:
        log_exception(e, "キャッシュの削除中にエラーが発生しました")
        return False


def has_valid_cache(file_path, config):
    """
    有効なキャッシュが存在するか確認する

    Args:
        file_path (str): 元のCSVファイルのパス
        config (dict): 現在の設定情報

    Returns:
        tuple: (キャッシュが存在する場合はTrue、キャッシュID)
    """
    try:
        if not config.get("use_cache", True):
            return False, None

        cache_id = generate_cache_id(file_path, config)
        cache_path = get_cache_path(file_path, cache_id)

        if os.path.exists(cache_path):
            # キャッシュファイルが存在する場合、その有効性を確認
            with open(cache_path, "rb") as f:
                data = pickle.load(f)

            # メタデータを確認
            metadata = data.get("_metadata", {})
            if metadata.get("app_version") != APP_VERSION:
                logger.warning(
                    f"キャッシュのバージョン({metadata.get('app_version')})が現在のバージョン({APP_VERSION})と一致しません"
                )
                return False, cache_id

            # ファイルの最終更新時間を確認
            file_mtime = os.path.getmtime(file_path)
            if metadata.get("file_mtime") != file_mtime:
                logger.warning(f"ファイルが更新されています: {file_path}")
                return False, cache_id

            logger.info(f"有効なキャッシュが見つかりました: {cache_path}")
            return True, cache_id
        else:
            logger.debug(f"キャッシュが見つかりません: {cache_path}")
            return False, cache_id

    except Exception as e:
        log_exception(e, "キャッシュの確認中にエラーが発生しました")
        return False, None
