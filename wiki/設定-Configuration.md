# 設定 - Configuration

このページでは、AATの設定ファイルと設定パラメータについて詳しく説明します。

---

## 📂 設定ファイルの場所

### ユーザー設定ファイル

AATの設定は、OS標準のユーザー設定ディレクトリに保存されます:

| OS | ファイルパス |
|----|-------------|
| **macOS** | `~/Library/Application Support/AAT/config.json` |
| **Windows** | `%APPDATA%\AAT\config.json` |
| **Linux** | `~/.config/AAT/config.json` または `$XDG_CONFIG_HOME/AAT/config.json` |

### 環境変数による上書き

環境変数`AAT_CONFIG_DIR`を設定することで、保存場所を変更できます:

```bash
# macOS/Linux
export AAT_CONFIG_DIR="~/custom/path/to/config"

# Windows (PowerShell)
$env:AAT_CONFIG_DIR="C:\custom\path\to\config"
```

### デフォルト設定ファイル

アプリケーションに同梱されているデフォルト設定:

```
AAT/config/config.default.json
```

このファイルは変更しないでください。ユーザー設定が存在しない場合、自動的にコピーされます。

---

## ⚙️ 設定パラメータ一覧

### データ処理設定

| パラメータ名 | 説明 | データ型 | デフォルト値 | 単位 |
|-------------|------|---------|-------------|------|
| **sampling_rate** | データのサンプリング周波数 | int | 1000 | Hz |
| **gravity_constant** | 基準重力加速度 | float | 9.797578 | m/s² |
| **acceleration_threshold** | 同期点検出に使う加速度閾値 | float | 5.0 | m/s² |
| **end_gravity_level** | フィルタリング終了閾値 | float | 8.0 | G |
| **min_seconds_after_start** | 開始点からスキップする最小秒数 | float | 0.7 | 秒 |
| **window_size** | 統計計算の時間窓 | float | 0.1 | 秒 |
| **invert_inner_acceleration** | Inner加速度の符号反転 | bool | true | - |

#### `sampling_rate`

データが何Hzでサンプリングされているかを指定します。

```json
{
  "sampling_rate": 1000
}
```

**影響範囲**:
- ウィンドウサイズのサンプル数計算
- 時間軸の変換

**推奨値**: データ取得時の実際のサンプリングレートに合わせる

#### `gravity_constant`

重力レベル計算の基準となる重力加速度です。

```json
{
  "gravity_constant": 9.797578
}
```

**計算式**:
```
重力レベル (G) = 加速度 (m/s²) / gravity_constant (m/s²)
```

**推奨値**: 実験環境の重力加速度に合わせる（地球標準: 9.80665 m/s²）

#### `acceleration_threshold`

Drag Shield/Inner の同期点検出に使用する閾値です。絶対値がこの値より小さい最初のサンプルを基準点（時間=0）とします。

```json
{
  "acceleration_threshold": 5.0
}
```

**補足**: 両方のセンサーで閾値未満のデータが見つからない場合は、先頭サンプルが使用されます。

#### `end_gravity_level`

データフィルタリングの終了閾値です。重力レベルがこの値以上になった時点で、それ以降のデータを切り捨てます。

```json
{
  "end_gravity_level": 8.0
}
```

**補足**: 値が大きいほど、より広い範囲のデータが保持されます。微小重力区間のみを厳密に抽出したい場合は、値を小さくしてください（例: 0.1）。

#### `min_seconds_after_start`

開始点（時間=0）から、終了点探索を開始するまでのスキップ時間（秒）です。実験開始直後の過渡応答を無視するために使用します。

```json
{
  "min_seconds_after_start": 0.7
}
```

#### `window_size`

統計計算時のスライディングウィンドウのサイズ（秒）です。この期間内のデータの標準偏差を計算し、最も安定した区間を探します。

```json
{
  "window_size": 0.1
}
```

**影響範囲**:
- `calculate_statistics()` 関数の結果
- テーブル表示・エクスポート時の「最小標準偏差」の計算対象区間

#### `invert_inner_acceleration`

Inner Capsuleの加速度データの符号を反転するかどうかを指定します。

```json
{
  "invert_inner_acceleration": true
}
```

**用途**: センサーの取り付け方向が逆の場合の補正。デフォルトで `true`（反転する）に設定されています。

#### G-quality 解析設定

G-quality評価モードで使用されるパラメータです。

```json
{
  "g_quality_start": 0.1,
  "g_quality_end": 1.0,
  "g_quality_step": 0.05
}
```

**動作**:
0.1秒から1.0秒まで、0.05秒刻みでウィンドウサイズを変更しながら統計解析を繰り返します（デフォルトでは19ステップ）。これにより、時間スケールごとの微小重力品質を評価できます。

---

### 機能設定

| パラメータ名 | 説明 | データ型 | デフォルト値 |
|-------------|------|---------|-------------|
| **use_cache** | キャッシュ機能の有効化 | bool | true |
| **auto_calculate_g_quality** | G-quality自動計算 | bool | true |
| **use_inner_acceleration** | Inner センサーを使用 | bool | true |
| **use_drag_acceleration** | Drag センサーを使用 | bool | true |

#### `use_cache`

処理済みデータをキャッシュして再利用するかを制御します。

```json
{
  "use_cache": true
}
```

**true**: キャッシュを使用（高速処理）
**false**: 常に再計算（デバッグ時など）

#### `auto_calculate_g_quality`

CSVファイル読み込み時に自動的にG-quality評価を実行するかを制御します。

```json
{
  "auto_calculate_g_quality": true
}
```

**true**: 自動実行
**false**: 手動実行のみ

#### `use_inner_acceleration` / `use_drag_acceleration`

```json
{
  "use_inner_acceleration": true,
  "use_drag_acceleration": true
}
```

どちらか一方でも `false` にすると、そのセンサー系列は読み込み・処理をスキップします（両方を `false` にするとエラーになります）。

---

### UI設定

| パラメータ名 | 説明 | データ型 | デフォルト値 |
|-------------|------|---------|-------------|
| **theme** | UIテーマ | string | "system" |
| **graph_sensor_mode** | グラフに表示するセンサー | string | "both" |

#### `theme`

UIのテーマを指定します。

```json
{
  "theme": "system"
}
```

**有効な値**:
- `"system"`: OSの設定に従う
- `"dark"`: ダークモード
- `"light"`: ライトモード

#### `graph_sensor_mode`

グラフに表示するセンサーを制御します。

```json
{
  "graph_sensor_mode": "both"
}
```

**有効な値**:
- `"both"`: 両方表示
- `"inner_only"`: Inner Capsuleのみ
- `"drag_only"`: Drag Shieldのみ

---

### エクスポート設定

| パラメータ名 | 説明 | データ型 | デフォルト値 | 単位 |
|-------------|------|---------|-------------|------|
| **export_figure_width** | グラフの幅 | int/float | 10.6 | インチ |
| **export_figure_height** | グラフの高さ | int/float | 3.4 | インチ |
| **export_dpi** | グラフの解像度 | int | 300 | DPI |

#### `export_figure_width` / `export_figure_height`

エクスポートされるグラフのサイズを制御します。

```json
{
  "export_figure_width": 10.6,
  "export_figure_height": 3.4
}
```

**推奨値**:
- スクリーン表示用: 10 × 6
- 論文用: 12 × 8
- プレゼン用: 16 × 9

#### `export_dpi`

グラフの解像度を指定します。

```json
{
  "export_dpi": 300
}
```

**推奨値**:
- スクリーン表示用: 150〜200
- 印刷用: 300〜600

---

## 🔧 設定の変更方法

### 方法1: 設定ダイアログ（推奨）

1. メニューバー「ファイル」→「設定」を選択
2. 各パラメータを変更
3. 「OK」をクリックして保存

### 方法2: JSONファイルを直接編集

1. 設定ファイルをテキストエディタで開く
2. JSONを編集
3. ファイルを保存
4. AATを再起動

**config.json の例**:

```json
{
    "time_column": "データセット1:時間(s)",
    "acceleration_column_inner_capsule": "データセット1:Z-axis acceleration 1(m/s²)",
    "acceleration_column_drag_shield": "データセット1:Z-axis acceleration 2(m/s²)",
    "use_inner_acceleration": true,
    "use_drag_acceleration": true,
    "sampling_rate": 1000,
    "gravity_constant": 9.797578,
    "acceleration_threshold": 5.0,
    "end_gravity_level": 8.0,
    "min_seconds_after_start": 0.7,
    "window_size": 0.1,
    "g_quality_start": 0.1,
    "g_quality_end": 1.0,
    "g_quality_step": 0.05,
    "use_cache": true,
    "auto_calculate_g_quality": true,
    "invert_inner_acceleration": true,
    "default_graph_duration": 1.45,
    "graph_sensor_mode": "both",
    "theme": "system",
    "export_figure_width": 10.6,
    "export_figure_height": 3.4,
    "export_dpi": 300,
    "export_bbox_inches": null
}
```

---

## 🔄 設定のリセット

設定ファイルを削除すると、次回起動時にデフォルト設定が自動的にコピーされます:

```bash
# macOS
rm ~/Library/Application\ Support/AAT/config.json

# Linux
rm ~/.config/AAT/config.json

# Windows (PowerShell)
Remove-Item "$env:APPDATA\AAT\config.json"
```

---

## 🛡️ バックアップと復元

### 自動バックアップ

設定を保存する際、既存の設定は自動的にバックアップされます:

```
config.json.bak
```

### 手動バックアップ

重要な設定変更前に手動でバックアップすることを推奨:

```bash
# macOS/Linux
cp ~/Library/Application\ Support/AAT/config.json ~/Library/Application\ Support/AAT/config.json.backup

# Windows (PowerShell)
Copy-Item "$env:APPDATA\AAT\config.json" "$env:APPDATA\AAT\config.json.backup"
```

---

## ⚠️ 注意事項

### 設定の影響範囲

設定を変更すると、既存のキャッシュが無効化され、次回読み込み時にデータが再計算されます。

### 無効な値

無効な値を設定すると、デフォルト値が使用されるか、エラーメッセージが表示されます。

### 文字エンコーディング

設定ファイルは**UTF-8**エンコーディングで保存してください。

---

## 🚀 次のステップ

- **[[使い方-Usage]]** - 設定を変更して動作を確認
- **[[データ解析パイプライン-Data-Analysis-Pipeline]]** - 設定がデータ処理に与える影響
- **[[トラブルシューティング-Troubleshooting]]** - 設定関連の問題と解決法
