# AAT APIリファレンス

このドキュメントでは、AAT (Acceleration Analysis Tool) のコアモジュールAPIをまとめます。GUI層から呼び出すときに必要となる入力・出力・前提条件を中心に記載しています。

## 目次

1. [data_processor - データ処理モジュール](#data_processor)
2. [statistics - 統計計算モジュール](#statistics)
3. [cache_manager - キャッシュ管理モジュール](#cache_manager)
4. [export - データエクスポートモジュール](#export)
5. [config - 設定管理モジュール](#config)
6. [logger - ロガーモジュール](#logger)
7. [exceptions - カスタム例外](#exceptions)
8. [version - バージョン情報ユーティリティ](#version)
9. [gui.styles - テーマ管理モジュール](#guistyles)
10. [基本ワークフロー例](#基本ワークフロー例)

---

## data_processor

データ処理の中核となるモジュール。CSVファイルからのデータ読み込み、列の自動検出、同期点検出、重力レベルへの変換、およびデータのフィルタリング機能を提供します。重力レベルは m/s² の加速度を `gravity_constant` で割った値（単位: G）として計算されます。

**主な責務**
- 列名のヒューリスティック検出（時間/加速度）と数値列へのフォールバック
- Inner Capsule 側の上下反転補正 (`invert_inner_acceleration`)
- Drag Shield 側の同期点検出 (`acceleration_threshold` 以下の最初のサンプル)
- 開始インデックス・終了インデックスの検出と個別トリミング

**前提となる設定キー**
`time_column`, `acceleration_column_inner_capsule`, `acceleration_column_drag_shield`, `gravity_constant`, `sampling_rate`, `acceleration_threshold`, `end_gravity_level`, `min_seconds_after_start`, `invert_inner_acceleration`

### 関数

#### `detect_columns(file_path: str) -> tuple[list[str], list[str]]`

CSVファイルから時間列と加速度列の候補を自動検出します。`time/time(s)/秒/sec` などのキーワードを優先し、見つからない場合は数値列を候補に含めます。

**パラメータ:**
- `file_path` (str): 解析対象のCSVファイルパス

**戻り値:**
- `tuple[list[str], list[str]]`: (時間列候補リスト, 加速度列候補リスト)

**例外:**
- `DataLoadError`: ファイルの読み込みに失敗した場合

**使用例:**
```python
time_columns, acc_columns = detect_columns("data.csv")
```

#### `load_and_process_data(file_path: str, config: dict[str, Any]) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]`

CSVファイルからデータを読み込み、加速度データを重力レベルに変換し、Drag Shield 側の同期点を検出して時間軸を調整します。Inner 側は同期点が見つからなければ Drag Shield と同じインデックスを使用します。

**パラメータ:**
- `file_path` (str): CSVファイルパス
- `config` (dict): 設定辞書（上記「前提となる設定キー」を参照）

**戻り値:**
- `tuple[pd.Series, pd.Series, pd.Series, pd.Series]`:
  - Inner Capsule調整済み時間データ (秒)
  - Inner Capsule重力レベル (G)
  - Drag Shield重力レベル (G)
  - Drag Shield調整済み時間データ (秒)

**例外:**
- `ColumnNotFoundError`: 指定された列が見つからない場合（GUI側で列選択ダイアログに分岐する想定）
- `DataProcessingError`: 両方のセンサーを無効にした場合など、処理継続ができない場合
- `DataLoadError`: その他のデータ読み込みエラー

**使用例（読み込み〜同期調整）**
```python
config = load_config()
adj_time_inner, g_inner, g_drag, adj_time_drag = load_and_process_data("data.csv", config)
```

#### `filter_data(time: pd.Series, gravity_level_inner_capsule: pd.Series, gravity_level_drag_shield: pd.Series, adjusted_time: pd.Series, config: dict[str, Any]) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, int]`

時間=0を基準にデータセットごとにトリミングし、`end_gravity_level` に達するまでのデータを抽出します。開始点から `min_seconds_after_start` まではスキップして微小重力安定後の区間だけを残します。

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

**補足**
- 内部ヘルパー `_find_start_indices` / `_find_end_indices` で開始・終了インデックスを決定します。外部から直接呼び出さないでください。

---

## statistics

重力レベルデータの統計分析機能を提供します。データ長チェックやウィンドウ長不足時の `None` 返却など、GUI側でのハンドリングを前提とした戻り値を持ちます。

### 関数

#### `calculate_statistics(gravity_level: pd.Series, time: pd.Series, config: dict[str, Union[float, int]]) -> tuple[Optional[float], Optional[float], Optional[float]]`

指定されたウィンドウサイズで標準偏差が最小となる時間窓を特定し、その区間の統計情報を計算します。`window_size` と `sampling_rate` からサンプル数を算出してスライディングウィンドウを構成します。

**パラメータ:**
- `gravity_level` (pd.Series): 重力レベルデータ
- `time` (pd.Series): 時間データ
- `config` (dict): 設定辞書
  - `window_size` (float): ウィンドウサイズ (秒、デフォルト: 0.1)
  - `sampling_rate` (int): サンプリングレート (Hz、デフォルト: 1000)

**戻り値:**
- `tuple[Optional[float], Optional[float], Optional[float]]`:
  - 最小標準偏差区間の絶対値平均 (G)
  - 最小標準偏差区間の開始時間 (秒)
  - 最小標準偏差値 (G)
  - データが不十分な場合は `(None, None, None)`

**例外:**
- `ValueError`: 時間データと重力レベルデータの長さが一致しない場合

**使用例（フィルタ済みデータから計算）**
```python
min_mean, min_time, min_std = calculate_statistics(filtered_inner, filtered_time, config)
```

#### `calculate_range_statistics(data_array: np.ndarray) -> dict[str, Optional[float]]`

ユーザーが範囲選択したデータに対して詳細な統計情報を計算します。空配列の場合は平均や標準偏差に `None` を返し、`count` を 0 とします。

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

処理済みデータのキャッシュを管理し、同じ設定・同じCSVでの再処理を高速化します。キャッシュの有効性はファイルの最終更新時刻とアプリケーションバージョン (`APP_VERSION`) で検証されます。

**キャッシュの妥当性判定**
- `use_cache` が `False` の場合は常に未使用扱い
- `generate_cache_id` で設定サブセットとファイルの更新時刻からID生成
- 保存済みメタデータ `_metadata` の `app_version` と `file_mtime` が一致しない場合は無効
- `raw_data` は別の HDF5 (`*_raw.h5`) に退避し、読み出し時に復元

### 関数

#### `generate_cache_id(file_path: str, config: dict) -> str`

ファイルパスと設定に基づいて一意のキャッシュIDを生成します。設定はキャッシュに影響するキーのみ（列名、閾値、アプリバージョンなど）をハッシュ化に使用します。

**パラメータ:**
- `file_path` (str): ファイルパス
- `config` (dict): 設定辞書

**戻り値:**
- `str`: SHA-256ハッシュによるキャッシュID（64文字の16進数文字列）

#### `get_cache_path(file_path: str, cache_id: str) -> str`

キャッシュファイルの保存パスを生成します。`results_AAT/cache` ディレクトリを必要に応じて作成します。

**パラメータ:**
- `file_path` (str): 元のCSVファイルパス
- `cache_id` (str): キャッシュID

**戻り値:**
- `str`: キャッシュファイルパス (`results_AAT/cache/{base_name}_{cache_id}.pickle`)

#### `save_to_cache(processed_data: dict, file_path: str, cache_id: str, config: dict) -> bool`

処理済みデータをキャッシュに保存します。大きな `raw_data` は HDF5 として別ファイルに保存し、pickle には含めません。保存時には同一CSVの古いキャッシュを削除します。

**パラメータ:**
- `processed_data` (dict): 保存するデータ辞書
- `file_path` (str): 元のCSVファイルパス
- `cache_id` (str): キャッシュID
- `config` (dict): 設定辞書

**戻り値:**
- `bool`: 成功時True、失敗時False

#### `load_from_cache(file_path: str, cache_id: str) -> Optional[dict]`

キャッシュからデータを読み込みます。メタデータが現在の `APP_VERSION` と一致しない場合や `raw_data` 復元に失敗した場合は `None` を返します。

**パラメータ:**
- `file_path` (str): 元のCSVファイルパス
- `cache_id` (str): キャッシュID

**戻り値:**
- `Optional[dict]`: キャッシュされたデータ辞書、存在しない場合はNone

#### `has_valid_cache(file_path: str, config: dict) -> tuple[bool, Optional[str]]`

有効なキャッシュの存在を確認します。ファイル更新時刻とアプリケーションバージョンまで検証します。

**パラメータ:**
- `file_path` (str): ファイルパス
- `config` (dict): 設定辞書

**戻り値:**
- `tuple[bool, Optional[str]]`: (キャッシュ存在フラグ, キャッシュIDまたはNone)

#### `delete_cache(file_path: str, cache_id: Optional[str] = None) -> bool`

指定されたキャッシュまたは対象CSVに紐づくすべてのキャッシュを削除します。`*_raw.h5` も併せて削除されます。

**パラメータ:**
- `file_path` (str): ファイルパス
- `cache_id` (Optional[str]): 削除するキャッシュID（Noneの場合このCSVの全キャッシュ）

**戻り値:**
- `bool`: 成功時True、失敗時False

**使用例（存在確認〜保存）**
```python
valid, cache_id = has_valid_cache(csv_path, config)
if valid:
    cached = load_from_cache(csv_path, cache_id)
else:
    cache_id = generate_cache_id(csv_path, config)
    save_to_cache(data_dict, csv_path, cache_id, config)
```

---

## export

処理済みデータと解析結果をExcelファイルにエクスポートします。出力ディレクトリ `results_AAT/`（`graphs/` を含む）をCSVと同じ階層に作成し、既存ファイルがある場合はコールバック経由で上書き確認を行います（GUI側でダイアログを差し込む前提の設計）。

**主な挙動**
- 保存時に時間軸を統一（`sampling_rate` からステップを算出し内外カプセルを補間）
- グラフ画像を `results_AAT/graphs/{base}_gl.png` にコピー
- `raw_data` が渡された場合、補間した加速度 (m/s²) を "Acceleration Data" シートに追加
- G-quality 用グラフは `{base}_gq.png` で保存

### 関数

#### `create_output_directories(csv_dir: Optional[str] = None) -> tuple[Path, Path]`

出力用のディレクトリ構造を作成します。`csv_dir` が空や None の場合はプロジェクトルートをフォールバックとして使用します。

**パラメータ:**
- `csv_dir` (Optional[str]): CSVファイルのディレクトリ（Noneの場合アプリケーションルート）

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
- `config` (Optional[dict[str, Any]]): 設定辞書（`sampling_rate` が補間に利用される）
- `raw_data` (Optional[pd.DataFrame]): 元のCSVデータ（シート "Acceleration Data" 用）
- `confirm_overwrite` (Optional[Callable[[Path], bool]]): 上書き可否を問い合わせるフック（未指定時は自動上書き）
- `notify_warning` (Optional[Callable[[str], None]]): 警告メッセージ通知用フック（未指定時はログ）
- `notify_info` (Optional[Callable[[str], None]]): 保存完了などの通知用フック（未指定時はログ）

**戻り値:**
- `str`: 出力されたExcelファイルのパス

**作成されるシート:**
- "Gravity Level Data": 補間後の重力レベルデータ
- "Gravity Level Statistics": 最小標準偏差区間の概要
- "Acceleration Data": 元の加速度データ（`raw_data` 提供時のみ）

#### `export_g_quality_data(g_quality_data: list[tuple], original_file_path: str, g_quality_graph_path: Optional[str] = None) -> Optional[str]`

G-quality解析結果を既存のExcelファイルに追加します。対象ファイルが無い場合はWorkbookを新規作成し、"G-quality Analysis" シートを書き換えます。

**パラメータ:**
- `g_quality_data` (list[tuple]): G-quality解析結果
  - `(window_size, min_time_inner_capsule, min_mean_inner_capsule, min_std_inner_capsule, min_time_drag_shield, min_mean_drag_shield, min_std_drag_shield)`
- `original_file_path` (str): 元のCSVファイルパス
- `g_quality_graph_path` (Optional[str]): G-qualityグラフのパス

**戻り値:**
- `Optional[str]`: 出力ファイルパス、失敗時はNone

---

## config

アプリケーション設定の読み込み・保存・移行を担うモジュール。ユーザー設定はOSの設定ディレクトリ（または `AAT_CONFIG_DIR`）に保存し、リポジトリ直下には書き込みません。

**補足**
- `_migrate_legacy_config`: 旧 `./config.json` を検出した場合にユーザー設定ディレクトリへ移動
- `get_user_config_dir`: 環境変数 `AAT_CONFIG_DIR` が指定されればそちらを優先し、作成に失敗した場合はホーム直下 `.AAT` に退避
- 設定保存時は `config.json.bak` を自動で作成し、書き込み失敗時にはバックアップから復元を試みる
- 結果出力やキャッシュ用のパス解決は `core.paths` で一元管理

### 関数

#### `load_config(on_warning: Optional[Callable[[str], None]] = None) -> dict[str, Any]`

デフォルト設定とユーザー設定をマージして返します。バージョン番号は常に `core.version.APP_VERSION` で上書きされます。

**パラメータ:**
- `on_warning` (Callable[[str], None], optional): 設定読み込み時の警告通知フック（GUI側でダイアログ表示を差し込む用途）

**戻り値:**
- `dict[str, Any]`: マージされた設定辞書

**設定ファイルの読み込み順序:**
1. `config/config.default.json` (デフォルト設定)
2. ユーザー設定ディレクトリ（mac: `~/Library/Application Support/AAT/config.json`, Windows: `%APPDATA%\\AAT\\config.json`, Linux/WSL: `$XDG_CONFIG_HOME/AAT/config.json`。`AAT_CONFIG_DIR` で上書き可）
3. 旧仕様の `./config.json` が残っている場合は自動的にユーザーディレクトリへ移行して読み込み

#### `save_config(config: dict[str, Any], on_error: Optional[Callable[[str], None]] = None) -> bool`

設定をJSONファイルに保存します。既存ファイルはバックアップを取り、浮動小数点の表記揺れを簡易的に補正してから書き込みます。

**パラメータ:**
- `config` (dict[str, Any]): 保存する設定辞書
- `on_error` (Callable[[str], None], optional): 保存失敗時の通知フック（GUI側でダイアログ表示を差し込む用途）

**戻り値:**
- `bool`: 成功時True、失敗時False

### デフォルト設定

```python
{
    "time_column": "データセット1:時間(s)",
    "acceleration_column_inner_capsule": "データセット1:Z-axis acceleration 1(m/s²)",
    "acceleration_column_drag_shield": "データセット1:Z-axis acceleration 2(m/s²)",
    "sampling_rate": 1000,
    "gravity_constant": 9.797578,
    "ylim_min": -1.0,
    "ylim_max": 1.0,
    "acceleration_threshold": 5.0,
    "end_gravity_level": 8.0,
    "window_size": 0.1,
    "g_quality_start": 0.1,
    "g_quality_end": 1.0,
    "g_quality_step": 0.05,
    "min_seconds_after_start": 0.7,
    "auto_calculate_g_quality": true,
    "use_cache": true,
    "default_graph_duration": 1.45,
    "export_figure_width": 10.6,
    "export_figure_height": 3.4,
    "export_dpi": 300,
    "export_bbox_inches": null,
    "invert_inner_acceleration": true,
    "app_version": "10.0.0"
}
```

`app_version` は実行時に `core.version.APP_VERSION` で上書きされるため、パッケージの更新に追随します。

---

## logger

アプリケーション全体で使用する統一的なロギング機能を提供します。`logging.basicConfig` で標準出力向けに初期化され、モジュールごとに名前空間を分離したロガーを取得できます。

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

例外情報を統一的な形式でログに記録します。`exc_info=True` でスタックトレースを含めます。

**パラメータ:**
- `e` (Exception): 記録する例外
- `message` (str): エラーメッセージ（デフォルト: "エラーが発生しました"）

### 環境変数とコマンドライン引数

- **`AAT_LOG_LEVEL`**: ログレベル設定 (DEBUG, INFO, WARNING, ERROR, CRITICAL)。設定がない場合はWARNING。
- **`AAT_DEBUG`**: デバッグモード有効化（1で有効、DEBUGレベル）
- **`--debug`**: コマンドライン引数でデバッグモード有効化
- **`--verbose` / `-v`**: 詳細出力モード（INFOレベル）

---

## exceptions

AATアプリケーション固有の例外クラスを定義します。GUI側でユーザー通知を行う際に例外種類に応じたメッセージを出し分けることを想定しています。

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
データ読み込み時の一般的なエラー。`file_path` を保持し、GUIのエラーダイアログに表示できます。

#### `ColumnNotFoundError`
必要な列が見つからない場合のエラー。`missing_columns` / `available_columns` を保持します。

**使用例:**
```python
raise ColumnNotFoundError(file_path, ["時間(s)"], df.columns.tolist())
```

### データ処理関連

#### `DataProcessingError`
データ処理時の一般的なエラー。`details` を付加して呼び出し元でのトラブルシュートを容易にします。

#### `SyncPointNotFoundError`
同期点が検出できない場合のエラー。例: センサー名を `sensor_type` に保持。

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

## version

バージョン情報を単一のソースから取得するためのユーティリティ。`core.config` やキャッシュ判定で利用されます。

### 定数

#### `APP_VERSION: str`
- 優先順位: インストール済みディストリビューションのメタデータ → `pyproject.toml` の `[project].version` → フォールバック `"0.0.0"`。
- Python 3.11 未満では tomllib が無い環境に備えたフォールバックも実装済み。

**使用例:**
```python
from core.version import APP_VERSION
print(f"AAT version: {APP_VERSION}")
```

---

## gui.styles

アプリケーションのテーマ（ダーク/ライト/システム）とカラーパレットを管理するモジュール。`QApplication` へのスタイル適用や、Matplotlib グラフの色設定を一元管理します。

### クラスと列挙型

#### `class ThemeType(Enum)`
- `DARK`: ダークモード
- `LIGHT`: ライトモード
- `SYSTEM`: システム設定に従う

#### `class Colors`
テーマに応じたカラーコード（16進数文字列）を保持するクラス。`set_theme(theme_type)` で値を更新します。
- `BG_PRIMARY`, `BG_SECONDARY`: 背景色
- `TEXT_PRIMARY`, `TEXT_SECONDARY`: 文字色
- `ACCENT_PRIMARY`: アクセントカラー
- `BORDER`: 境界線色

### 関数

#### `apply_theme(app: QApplication, theme: ThemeType = ThemeType.SYSTEM)`
指定されたテーマをアプリケーション全体に適用します。システムテーマの場合はOSの設定を検出して解決します。

---

## 基本ワークフロー例

典型的な処理の呼び出し順序の参考例です（例外処理は省略）。

```python
from core.config import load_config
from core.cache_manager import generate_cache_id, has_valid_cache, load_from_cache, save_to_cache
from core.data_processor import filter_data, load_and_process_data
from core.export import export_data
from core.statistics import calculate_statistics

config = load_config()
csv_path = "data.csv"

valid, cache_id = has_valid_cache(csv_path, config)
if valid:
    processed = load_from_cache(csv_path, cache_id)
else:
    adj_time_inner, g_inner, g_drag, adj_time_drag = load_and_process_data(csv_path, config)
    filtered_time, filtered_inner, filtered_drag, filtered_adj_time, end_idx = filter_data(
        adj_time_inner, g_inner, g_drag, adj_time_drag, config
    )
    min_mean_inner, min_time_inner, min_std_inner = calculate_statistics(filtered_inner, filtered_time, config)
    min_mean_drag, min_time_drag, min_std_drag = calculate_statistics(filtered_drag, filtered_adj_time, config)
    processed = {
        "time": adj_time_inner,
        "adjusted_time": adj_time_drag,
        "filtered_time": filtered_time,
        "filtered_adjusted_time": filtered_adj_time,
        "gravity_level_inner_capsule": g_inner,
        "gravity_level_drag_shield": g_drag,
        "filtered_gravity_level_inner_capsule": filtered_inner,
        "filtered_gravity_level_drag_shield": filtered_drag,
        "stats": {
            "inner": (min_mean_inner, min_time_inner, min_std_inner),
            "drag": (min_mean_drag, min_time_drag, min_std_drag),
        },
    }
    cache_id = generate_cache_id(csv_path, config)
    save_to_cache(processed, csv_path, cache_id, config)

export_data(
    processed["time"],
    processed["adjusted_time"],
    processed["gravity_level_inner_capsule"],
    processed["gravity_level_drag_shield"],
    csv_path,
    *processed["stats"]["inner"],
    *processed["stats"]["drag"],
    graph_path=None,
    filtered_time=processed["filtered_time"],
    filtered_adjusted_time=processed["filtered_adjusted_time"],
    config=config,
    raw_data=None,
)
```

---

## 設計パターンとベストプラクティス

- モジュール別ロガー: 各モジュールは専用のロガーを使い、発生源を明確化
- キャッシュシステム: アプリバージョンとファイル更新時刻でキャッシュを無効化して整合性を保持
- 例外階層: 例外種類に応じたUIメッセージやリトライの判断が可能
- 設定管理: デフォルト設定とユーザー設定を分離し、環境変数で保存先を上書き可能
- データパイプライン: 読み込み → 同期・補正 → フィルタリング → 統計 → エクスポート → キャッシュ

## スレッドセーフティ

- キャッシュ操作は基本的にシングルスレッドを想定
- GUI操作からのデータ処理は別スレッド（workers.py）で実行
- ロギングシステムはスレッドセーフ

最終更新日: 2025年11月22日
