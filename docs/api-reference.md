# AAT APIリファレンス

このドキュメントでは、AAT (Acceleration Analysis Tool) のコアモジュールのAPIについて詳しく説明します。

## 目次

1. [data_processor - データ処理モジュール](#data_processor)
2. [statistics - 統計計算モジュール](#statistics)
3. [cache_manager - キャッシュ管理モジュール](#cache_manager)
4. [export - データエクスポートモジュール](#export)
5. [config - 設定管理モジュール](#config)
6. [logger - ロガーモジュール](#logger)
7. [exceptions - カスタム例外](#exceptions)

---

## data_processor

データ処理の中核となるモジュール。CSVファイルからのデータ読み込み、列の自動検出、重力レベルへの変換、およびデータのフィルタリング機能を提供します。

### 関数

#### `detect_columns(file_path: str) -> tuple[list[str], list[str]]`

CSVファイルから時間列と加速度列の候補を自動検出します。

**パラメータ:**
- `file_path` (str): 解析対象のCSVファイルパス

**戻り値:**
- `tuple[list[str], list[str]]`: (時間列候補リスト, 加速度列候補リスト)

**例外:**
- `DataLoadError`: ファイルの読み込みに失敗した場合

**使用例:**
```python
time_columns, acc_columns = detect_columns("data.csv")
print(f"時間列候補: {time_columns}")
print(f"加速度列候補: {acc_columns}")
```

#### `load_and_process_data(file_path: str, config: dict[str, Any]) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]`

CSVファイルからデータを読み込み、加速度データを重力レベルに変換し、同期点を検出して時間軸を調整します。

**パラメータ:**
- `file_path` (str): CSVファイルパス
- `config` (dict): 設定辞書
  - `time_column` (str): 時間列名
  - `acceleration_column_inner_capsule` (str): Inner Capsule加速度列名
  - `acceleration_column_drag_shield` (str): Drag Shield加速度列名
  - `gravity_constant` (float): 重力定数 (m/s²)
  - `sampling_rate` (int): サンプリングレート (Hz)
  - `acceleration_threshold` (float): 同期点検出閾値 (m/s²)

**戻り値:**
- `tuple[pd.Series, pd.Series, pd.Series, pd.Series]`: 
  - Inner Capsule調整済み時間データ (秒)
  - Inner Capsule重力レベル (μG)
  - Drag Shield重力レベル (μG)
  - Drag Shield調整済み時間データ (秒)

**例外:**
- `ColumnNotFoundError`: 指定された列が見つからない場合
- `SyncPointNotFoundError`: 同期点が検出できない場合
- `DataLoadError`: その他のデータ読み込みエラー

#### `filter_data(time: pd.Series, gravity_level_inner_capsule: pd.Series, gravity_level_drag_shield: pd.Series, adjusted_time: pd.Series, config: dict[str, Any]) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, int]`

時間=0を基準にデータをトリミングし、指定された終了重力レベルまでのデータを抽出します。

**パラメータ:**
- `time` (pd.Series): 時間データ
- `gravity_level_inner_capsule` (pd.Series): Inner Capsule重力レベル
- `gravity_level_drag_shield` (pd.Series): Drag Shield重力レベル
- `adjusted_time` (pd.Series): 調整済み時間データ
- `config` (dict): 設定辞書
  - `end_gravity_level` (float): 終了重力レベル閾値
  - `min_seconds_after_start` (float): 開始後の最小秒数

**戻り値:**
- `tuple`: (フィルタ済み時間, フィルタ済みInner Capsule, フィルタ済みDrag Shield, フィルタ済み調整時間, 終了インデックス)

---

## statistics

重力レベルデータの統計分析機能を提供します。

### 関数

#### `calculate_statistics(gravity_level: pd.Series, time: pd.Series, config: dict[str, Union[float, int]]) -> tuple[Optional[float], Optional[float], Optional[float]]`

指定されたウィンドウサイズで標準偏差が最小となる時間窓を特定し、その区間の統計情報を計算します。

**パラメータ:**
- `gravity_level` (pd.Series): 重力レベルデータ
- `time` (pd.Series): 時間データ
- `config` (dict): 設定辞書
  - `window_size` (float): ウィンドウサイズ (秒、デフォルト: 0.1)
  - `sampling_rate` (int): サンプリングレート (Hz、デフォルト: 1000)

**戻り値:**
- `tuple[Optional[float], Optional[float], Optional[float]]`:
  - 最小標準偏差区間の絶対値平均 (μG)
  - 最小標準偏差区間の開始時間 (秒)
  - 最小標準偏差値 (μG)
  - データが不十分な場合は (None, None, None)

**例外:**
- `ValueError`: 時間データと重力レベルデータの長さが一致しない場合

#### `calculate_range_statistics(data_array: np.ndarray) -> dict[str, Optional[float]]`

選択範囲のデータに対して詳細な統計情報を計算します。

**パラメータ:**
- `data_array` (np.ndarray): 統計計算対象のデータ配列

**戻り値:**
- `dict[str, Optional[float]]`: 統計情報の辞書
  - `mean`: 平均値
  - `abs_mean`: 絶対値の平均
  - `std`: 標準偏差
  - `min`: 最小値
  - `max`: 最大値
  - `range`: 範囲（最大値 - 最小値）
  - `count`: データ点数

---

## cache_manager

処理済みデータのキャッシュを管理し、同じ設定での再処理を高速化します。

### 関数

#### `generate_cache_id(file_path: str, config: dict) -> str`

ファイルパスと設定に基づいて一意のキャッシュIDを生成します。

**パラメータ:**
- `file_path` (str): ファイルパス
- `config` (dict): 設定辞書

**戻り値:**
- `str`: SHA-256ハッシュによるキャッシュID（64文字の16進数文字列）

#### `get_cache_path(file_path: str, cache_id: str) -> str`

キャッシュファイルの保存パスを生成します。

**パラメータ:**
- `file_path` (str): 元のCSVファイルパス
- `cache_id` (str): キャッシュID

**戻り値:**
- `str`: キャッシュファイルパス (`results_AAT/cache/{base_name}_{cache_id}.pickle`)

#### `save_to_cache(processed_data: dict, file_path: str, cache_id: str, config: dict) -> bool`

処理済みデータをキャッシュに保存します。大きなデータはHDF5形式で別途保存されます。

**パラメータ:**
- `processed_data` (dict): 保存するデータ辞書
- `file_path` (str): 元のCSVファイルパス
- `cache_id` (str): キャッシュID
- `config` (dict): 設定辞書

**戻り値:**
- `bool`: 成功時True、失敗時False

#### `load_from_cache(file_path: str, cache_id: str) -> Optional[dict]`

キャッシュからデータを読み込みます。

**パラメータ:**
- `file_path` (str): 元のCSVファイルパス
- `cache_id` (str): キャッシュID

**戻り値:**
- `Optional[dict]`: キャッシュされたデータ辞書、存在しない場合はNone

#### `has_valid_cache(file_path: str, config: dict) -> tuple[bool, str]`

有効なキャッシュの存在を確認します。

**パラメータ:**
- `file_path` (str): ファイルパス
- `config` (dict): 設定辞書

**戻り値:**
- `tuple[bool, str]`: (キャッシュ存在フラグ, キャッシュID)

#### `delete_cache(file_path: str, cache_id: Optional[str] = None) -> bool`

指定されたキャッシュまたはすべてのキャッシュを削除します。

**パラメータ:**
- `file_path` (str): ファイルパス
- `cache_id` (Optional[str]): 削除するキャッシュID（Noneの場合すべて削除）

**戻り値:**
- `bool`: 成功時True、失敗時False

---

## export

処理済みデータと解析結果をExcelファイルにエクスポートする機能を提供します。

### 関数

#### `create_output_directories(csv_dir: Optional[str] = None) -> tuple[Path, Path]`

出力用のディレクトリ構造を作成します。

**パラメータ:**
- `csv_dir` (Optional[str]): CSVファイルのディレクトリ（Noneの場合カレントディレクトリ）

**戻り値:**
- `tuple[Path, Path]`: (results_dir, graphs_dir)のパス

#### `export_data(...) -> str`

重力レベルデータ、統計情報、加速度データをExcelファイルにエクスポートします。

**パラメータ:**
- `time` (pd.Series): 時間データ
- `adjusted_time` (pd.Series): 調整済み時間
- `gravity_level_inner_capsule` (pd.Series): Inner Capsule重力レベル
- `gravity_level_drag_shield` (pd.Series): Drag Shield重力レベル
- `file_path` (str): 元のCSVファイルパス
- `min_mean_inner_capsule` (Optional[float]): Inner Capsule最小標準偏差区間の絶対値平均
- `min_time_inner_capsule` (Optional[float]): Inner Capsule最小標準偏差区間の開始時間
- `min_std_inner_capsule` (Optional[float]): Inner Capsule最小標準偏差値
- `min_mean_drag_shield` (Optional[float]): Drag Shield最小標準偏差区間の絶対値平均
- `min_time_drag_shield` (Optional[float]): Drag Shield最小標準偏差区間の開始時間
- `min_std_drag_shield` (Optional[float]): Drag Shield最小標準偏差値
- `graph_path` (Optional[str]): グラフファイルのパス
- `filtered_time` (pd.Series): フィルタ済み時間データ
- `filtered_adjusted_time` (pd.Series): フィルタ済み調整時間データ
- `config` (Optional[dict[str, Any]]): 設定辞書
- `raw_data` (Optional[pd.DataFrame]): 元のCSVデータ

**戻り値:**
- `str`: 出力されたExcelファイルのパス

**作成されるシート:**
- "Gravity Level Data": 重力レベルデータ
- "Gravity Level Statistics": 統計情報
- "Acceleration Data": 元の加速度データ

#### `export_g_quality_data(g_quality_data: dict, original_file_path: str, g_quality_graph_path: Optional[str] = None) -> Optional[str]`

G-quality解析結果を既存のExcelファイルに追加します。

**パラメータ:**
- `g_quality_data` (dict): G-quality解析結果
- `original_file_path` (str): 元のCSVファイルパス
- `g_quality_graph_path` (Optional[str]): G-qualityグラフのパス

**戻り値:**
- `Optional[str]`: 出力ファイルパス、失敗時はNone

---

## config

アプリケーション設定の管理機能を提供します。

### 定数

#### `APP_VERSION`
- **型**: `str`
- **値**: `"9.1.0"`
- **説明**: アプリケーションのバージョン番号

### 関数

#### `load_config() -> dict[str, Any]`

設定ファイルを読み込み、デフォルト設定とユーザー設定をマージします。

**戻り値:**
- `dict[str, Any]`: マージされた設定辞書

**設定ファイルの読み込み順序:**
1. `config/config.default.json` (デフォルト設定)
2. `config.json` (ユーザー設定)

#### `save_config(config: dict[str, Any]) -> bool`

設定をJSONファイルに保存します。自動的にバックアップを作成します。

**パラメータ:**
- `config` (dict[str, Any]): 保存する設定辞書

**戻り値:**
- `bool`: 成功時True、失敗時False

### デフォルト設定

```python
{
    "time_column": "データセット1:時間(s)",
    "acceleration_column_inner_capsule": "データセット1:Z-axis acceleration 1(m/s²)",
    "acceleration_column_drag_shield": "データセット1:Z-axis acceleration 2(m/s²)",
    "sampling_rate": 1000,  # Hz
    "gravity_constant": 9.797578,  # m/s²
    "ylim_min": -1,  # グラフY軸最小値
    "ylim_max": 1,   # グラフY軸最大値
    "acceleration_threshold": 1.0,  # 同期点検出閾値 (m/s²)
    "end_gravity_level": 8,  # 終了重力レベル (μG)
    "window_size": 0.1,  # 統計計算ウィンドウサイズ (秒)
    "g_quality_start": 0.1,  # G-quality解析開始ウィンドウ (秒)
    "g_quality_end": 0.5,    # G-quality解析終了ウィンドウ (秒)
    "g_quality_step": 0.05,  # G-quality解析ステップ (秒)
    "min_seconds_after_start": 0.0,  # 開始後の最小秒数
    "auto_calculate_g_quality": True,  # 自動G-quality計算
    "use_cache": True,  # キャッシュ使用フラグ
    "app_version": "9.1.0"  # アプリケーションバージョン
}
```

---

## logger

アプリケーション全体で使用する統一的なロギング機能を提供します。

### 関数

#### `get_logger(module_name: str) -> logging.Logger`

モジュール専用のロガーインスタンスを取得します。

**パラメータ:**
- `module_name` (str): モジュール名

**戻り値:**
- `logging.Logger`: 設定済みのロガーインスタンス（名前空間: `AAT.{module_name}`）

**使用例:**
```python
from core.logger import get_logger
logger = get_logger(__name__)
logger.info("処理を開始します")
```

#### `log_exception(e: Exception, message: str = "エラーが発生しました") -> None`

例外情報を統一的な形式でログに記録します。

**パラメータ:**
- `e` (Exception): 記録する例外
- `message` (str): エラーメッセージ（デフォルト: "エラーが発生しました"）

### 環境変数とコマンドライン引数

- **`AAT_LOG_LEVEL`**: ログレベル設定 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **`AAT_DEBUG`**: デバッグモード有効化（1で有効）
- **`--debug`**: コマンドライン引数でデバッグモード有効化
- **`--verbose` / `-v`**: 詳細出力モード（INFOレベル）

---

## exceptions

AATアプリケーション固有の例外クラスを定義します。

### 例外クラス階層

```
AATException (基本例外クラス)
├── DataLoadError (データ読み込みエラー)
│   └── ColumnNotFoundError (必要な列が見つからない)
├── DataProcessingError (データ処理エラー)
│   ├── SyncPointNotFoundError (同期点が見つからない)
│   └── InsufficientDataError (データ不足)
├── ConfigurationError (設定関連エラー)
├── ExportError (エクスポートエラー)
└── CacheError (キャッシュ操作エラー)
```

### 基本例外クラス

#### `AATException`

すべてのAAT固有例外の基底クラス。

**属性:**
- `message` (str): エラーメッセージ
- `details` (Optional[dict]): 追加の詳細情報

**メソッド:**
- `__str__()`: フォーマットされたエラーメッセージを返す

### データ読み込み関連

#### `DataLoadError`
データ読み込み時の一般的なエラー。

#### `ColumnNotFoundError`
必要な列が見つからない場合のエラー。

**使用例:**
```python
raise ColumnNotFoundError(
    "時間列が見つかりません",
    details={"file": "data.csv", "expected_column": "時間(s)"}
)
```

### データ処理関連

#### `DataProcessingError`
データ処理時の一般的なエラー。

#### `SyncPointNotFoundError`
同期点が検出できない場合のエラー。

#### `InsufficientDataError`
データが不足している場合のエラー。

### その他のエラー

#### `ConfigurationError`
設定ファイルや設定値に関するエラー。

#### `ExportError`
データのエクスポート時のエラー。

#### `CacheError`
キャッシュの読み書き時のエラー。

---

## 設計パターンとベストプラクティス

### モジュール別ロガー
各モジュールは専用のロガーを使用し、デバッグとトラブルシューティングを容易にします。

### キャッシュシステム
処理済みデータをキャッシュすることで、同じ設定での再処理を高速化します。

### 例外階層
詳細なエラー情報とエラータイプの分類により、適切なエラーハンドリングが可能です。

### 設定管理
デフォルト設定とユーザー設定を分離し、設定の永続性と柔軟性を実現します。

### データパイプライン
明確に定義されたデータ処理フロー：読み込み → 処理 → フィルタリング → 統計 → エクスポート

## スレッドセーフティ

- キャッシュ操作は基本的にシングルスレッドを想定
- GUI操作からのデータ処理は別スレッド（workers.py）で実行
- ロギングシステムはスレッドセーフ