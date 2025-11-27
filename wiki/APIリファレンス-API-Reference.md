# APIリファレンス - API Reference

このページでは、AATのコアモジュールのAPI仕様を説明します。

> [!NOTE]
> より詳細な情報は [docs/api-reference.md](https://github.com/sata04/AAT/blob/main/docs/api-reference.md) をご覧ください。

---

## 📚 モジュール一覧

- **[[#core.data_processor]]** - データ読み込みと処理
- **[[#core.statistics]]** - 統計計算
- **[[#core.cache_manager]]** - キャッシュ管理
- **[[#core.export]]** - データエクスポート
- **[[#core.config]]** - 設定管理
- **[[#core.exceptions]]** - カスタム例外

---

## core.data_processor

CSVファイルからのデータ読み込みと重力レベル計算を担当します。

### `detect_columns(file_path: str)`

CSVファイルから時間列と加速度列の候補を検出します。

**パラメータ**:
- `file_path` (str): CSVファイルのパス

**戻り値**:
- `tuple[list, list]`: (時間列候補, 加速度列候補)

**例外**:
- `ValueError`: 列検出中にエラーが発生

**使用例**:

```python
from core.data_processor import detect_columns

time_cols, accel_cols = detect_columns('data.csv')
print(f"時間列候補: {time_cols}")
print(f"加速度列候補: {accel_cols}")
```

### `load_and_process_data(file_path: str, config: dict)`

CSVファイルからデータを読み込み、重力レベルに変換します。

**パラメータ**:
- `file_path` (str): CSVファイルのパス
- `config` (dict): 設定パラメータ

**戻り値**:
- `tuple`: (gravity_level_inner, gravity_level_drag, time, adjusted_time)

**例外**:
- `DataLoadError`: データ読み込み失敗
- `ColumnNotFoundError`: 必要な列が見つからない

**使用例**:

```python
from core.data_processor import load_and_process_data
from core.config import load_config

config = load_config()
gl_inner, gl_drag, time, adj_time = load_and_process_data('data.csv', config)
```

### `filter_data(...)`

データをフィルタリングして微小重力環境の範囲を抽出します。

詳細は [APIドキュメント](https://github.com/sata04/AAT/blob/main/docs/api-reference.md) を参照してください。

---

## core.statistics

統計計算を担当します。

### `calculate_statistics(gravity_level: pd.Series, time: pd.Series, config: dict)`

スライディングウィンドウで統計情報を計算します。

**パラメータ**:
- `gravity_level` (pd.Series): 重力レベルデータ
- `time` (pd.Series): 時間データ
- `config` (dict): 設定パラメータ

**戻り値**:
- `tuple[float | None, float | None, float | None]`: (平均G, 開始時間, 標準偏差)

**使用例**:

```python
from core.statistics import calculate_statistics

mean_g, start_time, std_dev = calculate_statistics(
    gravity_level, time,
    {'window_size': 0.1, 'sampling_rate': 1000}
)
```

### `calculate_range_statistics(data_array: np.ndarray)`

選択範囲の統計情報を計算します。

**戻り値**:
- `dict[str, float | None]`: 統計情報の辞書

---

## core.cache_manager

キャッシュ管理を担当します。

### `generate_cache_id(file_path: str, config: dict)`

設定とファイル情報からキャッシュIDを生成します。

### `save_to_cache(processed_data: dict, file_path: str, cache_id: str, config: dict)`

処理済みデータをキャッシュに保存します。

### `load_from_cache(file_path: str, cache_id: str)`

キャッシュからデータを読み込みます。

### `has_valid_cache(file_path: str, config: dict)`

有効なキャッシュが存在するか確認します。

**使用例**:

```python
from core.cache_manager import has_valid_cache, load_from_cache
from core.config import load_config

config = load_config()
has_cache, cache_id = has_valid_cache('data.csv', config)

if has_cache:
    data = load_from_cache('data.csv', cache_id)
```

---

## core.export

Excel/グラフのエクスポートを担当します。

### `export_data(...)`

処理済みデータをExcelファイルとグラフ画像にエクスポートします。

**主要パラメータ**:
- `time`, `gravity_level_inner`, `gravity_level_drag`: データ
- `statistics_inner`, `statistics_drag`: 統計情報
- `output_file_path`: 出力ファイルパス
- `config`: 設定情報

### `export_g_quality_data(g_quality_data: dict, original_file_path: str, ...)`

G-quality評価結果をExcelに追加します。

---

## core.config

設定管理を担当します。

### `load_config()`

設定ファイルを読み込みます。

**戻り値**:
- `dict[str, Any]`: 設定情報

**使用例**:

```python
from core.config import load_config, save_config

# 設定の読み込み
config = load_config()

# 設定の変更
config['sampling_rate'] = 2000

# 設定の保存
save_config(config)
```

### `save_config(config: dict)`

設定をファイルに保存します。

### `get_user_config_dir()`

ユーザー設定ディレクトリのパスを取得します。

---

## core.exceptions

カスタム例外クラスを定義します。

### `DataLoadError`

データ読み込み時のエラー。

**使用例**:

```python
from core.exceptions import DataLoadError

try:
    data = load_csv_file(path)
except DataLoadError as e:
    print(f"データ読み込みエラー: {e}")
```

### `DataProcessingError`

データ処理時のエラー。

### `ColumnNotFoundError`

必要な列が見つからない場合のエラー。

---

## 🧪 使用例

### 完全なデータ処理フロー

```python
import pandas as pd
from core.config import load_config
from core.data_processor import load_and_process_data, filter_data
from core.statistics import calculate_statistics
from core.cache_manager import has_valid_cache, load_from_cache, save_to_cache, generate_cache_id
from core.export import export_data

# 設定の読み込み
config = load_config()

# キャッシュチェック
file_path = 'experiment_data.csv'
has_cache, cache_id = has_valid_cache(file_path, config)

if has_cache and config.get('use_cache', True):
    # キャッシュから読み込み
    data = load_from_cache(file_path, cache_id)
else:
    # データ処理
    gl_inner, gl_drag, time, adj_time = load_and_process_data(file_path, config)

    # フィルタリング
    time_f, gl_inner_f, gl_drag_f, adj_time_f, _, _ = filter_data(
        time, gl_inner, gl_drag, adj_time, config
    )

    # 統計計算
    stats_inner = calculate_statistics(gl_inner_f, time_f, config)
    stats_drag = calculate_statistics(gl_drag_f, adj_time_f, config)

    # キャッシュに保存
    cache_id = generate_cache_id(file_path, config)
    processed_data = {
        'time': time_f,
        'gravity_level_inner': gl_inner_f,
        'gravity_level_drag': gl_drag_f,
        'adjusted_time': adj_time_f,
        'statistics_inner': stats_inner,
        'statistics_drag': stats_drag
    }
    save_to_cache(processed_data, file_path, cache_id, config)

# 結果をエクスポート
export_data(
    time_f, gl_inner_f, gl_drag_f, adj_time_f,
    stats_inner, stats_drag,
    'results_AAT/output.xlsx',
    file_path, config
)
```

---

## 📖 詳細ドキュメント

より詳細なAPI仕様は、以下のドキュメントを参照してください:

- [docs/api-reference.md](https://github.com/sata04/AAT/blob/main/docs/api-reference.md) - 完全なAPIリファレンス
- [docs/developer-guide.md](https://github.com/sata04/AAT/blob/main/docs/developer-guide.md) - 開発者向けガイド

---

## 🚀 次のステップ

- **[[開発者ガイド-Developer-Guide]]** - 開発環境のセットアップ
- **[[プロジェクト構造-Project-Structure]]** - モジュール構成
- **[[使用例-Examples]]** - 実践的な使用例

[[Home]] に戻る
