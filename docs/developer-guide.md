# AAT 開発者ガイド

## 目次

1. [はじめに](#はじめに)
2. [開発環境のセットアップ](#開発環境のセットアップ)
3. [プロジェクト構造](#プロジェクト構造)
4. [アーキテクチャ概要](#アーキテクチャ概要)
5. [コーディング規約](#コーディング規約)
6. [開発ワークフロー](#開発ワークフロー)
7. [新機能の追加](#新機能の追加)
8. [テスト](#テスト)
9. [デバッグ](#デバッグ)
10. [パフォーマンス最適化](#パフォーマンス最適化)
11. [リリースプロセス](#リリースプロセス)
12. [よくある開発タスク](#よくある開発タスク)

---

## はじめに

このガイドは、AATの開発に参加する開発者向けのドキュメントです。プロジェクトの構造、開発環境の構築、コーディング規約、テスト方法などについて説明します。

### 前提条件

- Python 3.9以降の知識
- PySide6の基本的な理解
- Gitの使用経験
- 微小重力実験データの基礎知識（推奨）

---

## 開発環境のセットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/sata04/AAT.git
cd AAT
```

### 2. Python仮想環境の作成

#### uvを使用する場合（推奨）
```bash
# uvのインストール
pip install uv

# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate  # Windows
```

#### venvを使用する場合
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate  # Windows
```

### 3. 依存関係のインストール

```bash
# 開発用依存関係（ruff、pytest、types-openpyxl等を含む）
uv pip install -e ".[dev]"

# uvを使わない場合
pip install -e ".[dev]"
```

### 4. pre-commitフックの設定

```bash
# フックの設定（uv経由）
uv run pre-commit install

# 手動実行（オプション）
uv run pre-commit run --all-files
```

### 5. VSCode設定（推奨）

プロジェクトには`.vscode/settings.json`が含まれています。以下の拡張機能をインストールしてください：

```bash
code --install-extension charliermarsh.ruff
code --install-extension ms-python.python
code --install-extension ms-python.debugpy
```

### 6. 開発環境の確認

```bash
# アプリケーションの起動確認
uv run python main.py --debug

# コード品質チェック
uv run ruff check .
uv run ruff format .

# テストの実行（tests/ を作成した場合）
uv run pytest -v
```

---

## プロジェクト構造

```
AAT/
├── core/                          # コアロジック
│   ├── __init__.py               # パッケージ初期化
│   ├── cache_manager.py          # キャッシュ管理
│   ├── config.py                 # 設定管理
│   ├── data_processor.py         # データ処理
│   ├── exceptions.py             # カスタム例外
│   ├── export.py                 # データエクスポート
│   ├── logger.py                 # ロギング
│   ├── statistics.py             # 統計計算
│   └── version.py                # バージョン取得ヘルパー
├── gui/                          # GUI関連
│   ├── __init__.py              # パッケージ初期化
│   ├── main_window.py           # メインウィンドウ
│   ├── workers.py               # バックグラウンドワーカー
│   ├── settings_dialog.py       # 設定ダイアログ
│   ├── column_selector_dialog.py # 列選択ダイアログ
│   └── styles.py                # テーマ設定
├── config/                       # 設定ファイル
│   ├── config.default.json      # デフォルト設定
│   └── （ユーザー設定はOS標準の設定ディレクトリに保存）
├── docs/                        # ドキュメント
├── tests/                       # テストを追加する場合に作成
├── .github/                     # GitHub Actions設定
│   └── workflows/
│       └── ruff.yml            # Ruffチェック
├── .vscode/                    # VSCode設定
├── main.py                     # エントリーポイント
├── pyproject.toml              # プロジェクト設定
├── uv.lock                     # 依存関係ロックファイル
├── README.md                   # プロジェクトREADME
├── AGENTS.md                   # 開発ガイドライン
└── LICENSE.md                  # ライセンス
```

ユーザー設定（`config.json`）は `core.config.get_user_config_dir()` が返すOS標準の設定ディレクトリに保存されます（mac: `~/Library/Application Support/AAT/`、Windows: `%APPDATA%\\AAT\\`、Linux/WSL: `$XDG_CONFIG_HOME/AAT/`）。保存先を変えたい場合は環境変数 `AAT_CONFIG_DIR` で上書きできます。

---

## アーキテクチャ概要

### レイヤードアーキテクチャ

AATは3層のレイヤードアーキテクチャを採用しています：

```
┌─────────────────────────────────────┐
│      GUI Layer (gui/)               │
│  - PySide6ベースのユーザーインターフェース    │
│  - ユーザー操作の処理                   │
│  - データの視覚化                      │
├─────────────────────────────────────┤
│      Core Layer (core/)             │
│  - ビジネスロジック                     │
│  - データ処理アルゴリズム                │
│  - ファイルI/O                        │
├─────────────────────────────────────┤
│      Infrastructure                 │
│  - 設定管理                          │
│  - ロギング                          │
│  - キャッシュ                         │
└─────────────────────────────────────┘
```

### 主要コンポーネント

#### 1. データ処理パイプライン
```
CSV読込 → 列検出 → 同期点検出 → 重力レベル変換 → フィルタリング → 統計計算 → エクスポート
```

#### 2. GUI更新フロー
```
ユーザー操作 → Signalエミット → Slotで処理 → UIスレッドで更新
```

#### 3. バックグラウンド処理
```
重い処理 → QThreadWorker → 進捗Signal → プログレスバー更新
```

#### 4. テーマ管理
```
設定/OS → ThemeType → Styles.py → QPalette/StyleSheet適用
```

### 設計原則

1. **関心の分離**: GUIとビジネスロジックの完全分離
2. **単一責任の原則**: 各モジュールは明確な責任を持つ
3. **依存性逆転**: 上位層は下位層の抽象に依存
4. **DRY原則**: コードの重複を避ける

---

## コーディング規約

### Python Style Guide

プロジェクトはRuffを使用してコード品質を管理しています。

#### 基本ルール
- インデント: スペース4つ
- 行長: 最大120文字 (Ruff設定)
- 文字列: ダブルクォート使用
- インポート: isortルールに従う

#### 命名規則
```python
# クラス名: PascalCase
class DataProcessor:
    pass

# 関数・変数名: snake_case
def calculate_gravity_level(acceleration):
    sampling_rate = 1000
    return acceleration / GRAVITY_CONSTANT

# 定数: UPPER_SNAKE_CASE
GRAVITY_CONSTANT = 9.79758

# プライベート: 先頭にアンダースコア
def _internal_function():
    pass
```

### 型ヒント

すべての関数に型ヒントを追加してください：

```python
from typing import Optional, Union, Dict, List, Tuple
import pandas as pd

def process_data(
    file_path: str,
    config: Dict[str, Any],
    use_cache: bool = True
) -> Tuple[pd.Series, pd.Series]:
    """
    データを処理して重力レベルを計算
    
    Args:
        file_path: CSVファイルパス
        config: 設定辞書
        use_cache: キャッシュ使用フラグ
        
    Returns:
        Inner CapsuleとDrag Shieldの重力レベル
    """
    pass
```

### ドキュメンテーション

#### モジュールレベル
```python
"""
data_processor.py - データ処理モジュール

このモジュールは、CSVファイルからのデータ読み込み、
列の自動検出、重力レベルへの変換機能を提供します。
"""
```

#### 関数・メソッド
```python
def detect_columns(file_path: str) -> Tuple[List[str], List[str]]:
    """
    CSVファイルから時間列と加速度列を自動検出
    
    キーワードベースの列検出アルゴリズムを使用して、
    時間列と加速度列の候補を特定します。
    
    Args:
        file_path: 解析対象のCSVファイルパス
        
    Returns:
        (時間列候補リスト, 加速度列候補リスト)のタプル
        
    Raises:
        DataLoadError: ファイル読み込みエラー
        
    Example:
        >>> time_cols, acc_cols = detect_columns("data.csv")
        >>> print(f"時間列: {time_cols[0]}")
    """
    pass
```

### エラーハンドリング

```python
from core.exceptions import DataLoadError, ColumnNotFoundError
from core.logger import get_logger

logger = get_logger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    try:
        # ファイル読み込み処理
        df = pd.read_csv(file_path)
        logger.info(f"データ読み込み成功: {file_path}")
        return df
    except FileNotFoundError as e:
        logger.error(f"ファイルが見つかりません: {file_path}")
        raise DataLoadError(
            f"ファイルが見つかりません: {file_path}",
            details={"file_path": file_path, "error": str(e)}
        )
    except pd.errors.ParserError as e:
        logger.error(f"CSV解析エラー: {e}")
        raise DataLoadError(
            "CSVファイルの形式が不正です",
            details={"file_path": file_path, "error": str(e)}
        )
```

### PySide6のベストプラクティス

#### Signalとslotの定義
```python
class MainWindow(QMainWindow):
    # Signalは クラスレベルで定義
    data_loaded = Signal(str)
    progress_updated = Signal(int)
    
    def __init__(self):
        super().__init__()
        # Signal接続は初期化時に
        self.data_loaded.connect(self.on_data_loaded)
        
    @Slot(str)
    def on_data_loaded(self, file_path: str):
        """データ読み込み完了時の処理"""
        pass
```

#### スレッド処理
```python
class DataProcessingWorker(QThread):
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, file_path: str, config: dict):
        super().__init__()
        self.file_path = file_path
        self.config = config
        
    def run(self):
        try:
            # 重い処理
            for i in range(100):
                self.progress.emit(i)
                # 処理...
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

---

## 開発ワークフロー

### 1. ブランチ戦略

```bash
# 新機能開発
git checkout -b feature/feature-name

# バグ修正
git checkout -b fix/bug-description

# ドキュメント更新
git checkout -b docs/update-description
```

### 2. コミットメッセージ

Conventional Commitsに従ってください：

```bash
# 新機能
git commit -m "feat: G-quality解析の自動実行オプションを追加"

# バグ修正
git commit -m "fix: 同期点検出の精度を改善"

# ドキュメント
git commit -m "docs: API リファレンスを更新"

# リファクタリング
git commit -m "refactor: データ処理パイプラインを最適化"

# テスト
git commit -m "test: 統計計算のユニットテストを追加"

# ビルド・CI
git commit -m "ci: GitHub Actions ワークフローを更新"
```

### 3. コード品質チェック

```bash
# Ruffでリント
ruff check .

# 自動修正
ruff check . --fix

# フォーマット
ruff format .

# pre-commitで全チェック
pre-commit run --all-files
```

### 4. プルリクエスト

1. フォークまたはブランチを作成
2. 変更を実装
3. テストを追加/更新
4. ドキュメントを更新
5. プルリクエストを作成

PR テンプレート：
```markdown
## 概要
変更の簡潔な説明

## 変更内容
- [ ] 機能A を実装
- [ ] バグB を修正
- [ ] テストを追加

## テスト方法
1. アプリケーションを起動
2. 〇〇を実行
3. △△が表示されることを確認

## スクリーンショット（該当する場合）
変更前後の画面キャプチャ

## チェックリスト
- [ ] コードがプロジェクトのスタイルガイドに従っている
- [ ] 自己レビューを実施した
- [ ] コメントを追加した（特に複雑な部分）
- [ ] ドキュメントを更新した
- [ ] 変更によって既存機能が壊れていない
- [ ] テストが正常に通る
```

---

## 新機能の追加

### 例: 新しい統計指標の追加

#### 1. core/statistics.pyに関数を追加

```python
def calculate_rms(data: np.ndarray) -> float:
    """
    Root Mean Square（二乗平均平方根）を計算
    
    Args:
        data: 入力データ配列
        
    Returns:
        RMS値
    """
    return np.sqrt(np.mean(data ** 2))
```

#### 2. データ処理に組み込み

```python
# core/data_processor.py
def process_statistics(gravity_level: pd.Series, config: dict) -> dict:
    # 既存の統計計算
    stats = calculate_statistics(gravity_level, time, config)
    
    # 新しい指標を追加
    rms_value = calculate_rms(gravity_level.values)
    stats['rms'] = rms_value
    
    return stats
```

#### 3. GUIに表示を追加

```python
# gui/main_window.py
def update_statistics_table(self, stats: dict):
    # 既存の行に加えて
    rms_row = self.table.rowCount()
    self.table.insertRow(rms_row)
    self.table.setItem(rms_row, 0, QTableWidgetItem("RMS"))
    self.table.setItem(rms_row, 1, QTableWidgetItem(f"{stats['rms']:.3f}"))
```

#### 4. エクスポートに追加

```python
# core/export.py
def export_statistics(stats: dict, worksheet):
    # 既存のエクスポートに追加
    worksheet.append(["RMS", stats.get('rms', 'N/A')])
```

#### 5. テストを作成

```python
# tests/test_statistics.py
def test_calculate_rms():
    data = np.array([1, -1, 1, -1])
    result = calculate_rms(data)
    assert result == 1.0
```

---

## テスト

### テスト構造

```
tests/
├── unit/                   # ユニットテスト
│   ├── test_data_processor.py
│   ├── test_statistics.py
│   └── test_cache_manager.py
├── integration/           # 統合テスト
│   ├── test_pipeline.py
│   └── test_export.py
└── gui/                   # GUIテスト
    ├── test_main_window.py
    └── test_dialogs.py
```

### ユニットテストの作成

```python
import pytest
from core.statistics import calculate_statistics

class TestStatistics:
    @pytest.fixture
    def sample_data(self):
        """テスト用サンプルデータ"""
        time = pd.Series(np.arange(0, 1, 0.001))
        gravity = pd.Series(np.random.normal(0, 0.1, 1000))
        return time, gravity
        
    def test_calculate_statistics_normal(self, sample_data):
        """正常系テスト"""
        time, gravity = sample_data
        config = {"window_size": 0.1, "sampling_rate": 1000}
        
        mean_abs, start_time, min_std = calculate_statistics(
            gravity, time, config
        )
        
        assert mean_abs is not None
        assert 0 <= start_time <= 0.9
        assert min_std > 0
        
    def test_calculate_statistics_empty_data(self):
        """空データのテスト"""
        time = pd.Series([])
        gravity = pd.Series([])
        config = {"window_size": 0.1, "sampling_rate": 1000}
        
        result = calculate_statistics(gravity, time, config)
        assert result == (None, None, None)
```

### GUIテスト

```python
import pytest
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from gui.main_window import MainWindow

@pytest.fixture
def main_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_file_selection_button(main_window, qtbot):
    """ファイル選択ボタンのテスト"""
    # ボタンをクリック
    qtbot.mouseClick(
        main_window.select_file_button,
        Qt.MouseButton.LeftButton
    )
    
    # ダイアログが開くことを確認（モック化が必要）
    assert main_window.file_dialog_opened
```

### テストの実行

```bash
# すべてのテストを実行
pytest

# 特定のテストを実行
pytest tests/unit/test_statistics.py

# カバレッジ付きで実行
pytest --cov=core --cov=gui --cov-report=html

# GUIテストのみ実行
pytest -m gui

# 遅いテストをスキップ
pytest -m "not slow"

### カスタムマーカー
- `slow`: 実行に時間がかかるテスト（パフォーマンステスト等）
- `gui`: GUIコンポーネントを必要とするテスト（Qtバックエンドが必要）
```

---

## デバッグ

### ロギングの活用

```python
from core.logger import get_logger

logger = get_logger(__name__)

def process_data(file_path: str):
    logger.debug(f"処理開始: {file_path}")
    
    try:
        # 処理
        logger.info(f"処理成功: {record_count}件")
    except Exception as e:
        logger.error(f"処理失敗: {e}", exc_info=True)
        raise
```

### デバッグモードの使用

```bash
# デバッグログを有効化
uv run python main.py --debug

# 環境変数で設定
AAT_DEBUG=1 uv run python main.py

# ログレベルを指定
AAT_LOG_LEVEL=DEBUG uv run python main.py
```

### VSCodeでのデバッグ

`.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: AAT Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--debug"],
            "console": "integratedTerminal",
            "env": {
                "AAT_DEBUG": "1"
            }
        }
    ]
}
```

### プロファイリング

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # プロファイル対象の処理
    process_large_dataset()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 上位20個を表示
```

---

## パフォーマンス最適化

### 1. データ処理の最適化

```python
# 悪い例: ループでの処理
def calculate_slow(data):
    result = []
    for value in data:
        result.append(value / GRAVITY_CONSTANT * 1e6)
    return result

# 良い例: ベクトル化
def calculate_fast(data: pd.Series) -> pd.Series:
    return data / GRAVITY_CONSTANT * 1e6
```

### 2. キャッシュの活用

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(window_size: float, sampling_rate: int):
    # 高コストな計算
    return result
```

### 3. 非同期処理

```python
class AsyncDataLoader(QThread):
    def __init__(self, file_paths: List[str]):
        super().__init__()
        self.file_paths = file_paths
        
    def run(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for path in self.file_paths:
                future = executor.submit(self.load_file, path)
                futures.append(future)
                
            for future in as_completed(futures):
                result = future.result()
                self.file_loaded.emit(result)
```

### 4. メモリ使用量の削減

```python
# チャンク処理でメモリ使用量を制限
def process_large_file(file_path: str, chunk_size: int = 10000):
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # チャンクごとに処理
        processed = process_chunk(chunk)
        yield processed
```

---

## リリースプロセス

### 1. バージョン番号の更新

`core/version.APP_VERSION`が参照する単一ソースは`pyproject.toml`の`[project].version`です。ここを更新すると、キャッシュ無効化やUI表示に自動反映されます。

```toml
[project]
version = "10.0.0"  # Major.Minor.Patch
```

### 2. 変更履歴の更新

CHANGELOG.mdに変更内容を記載：
```markdown
## [10.0.0] - 2025-11-22

### Added
- 新機能の説明

### Changed
- 変更点の説明

### Fixed
- 修正したバグの説明
```

### 3. テストの実行

```bash
# フルテストスイート
pytest

# リグレッションテスト
pytest tests/regression/
```

### 4. ビルド

```bash
# パッケージのビルド
uv run python -m build

# 実行可能ファイルの作成（PyInstaller使用）
uv run pyinstaller --onefile --windowed main.py
```

### 5. タグ付けとリリース

```bash
# タグの作成
git tag -a v10.0.0 -m "Release version 10.0.0"

# GitHubへプッシュ
git push origin v10.0.0

# GitHub Releasesでリリースノートを作成
```

---

## よくある開発タスク

### 新しい設定項目の追加

1. デフォルト値を定義
```python
# core/config.py のDEFAULT_CONFIG に追加
"new_option": False,
```

2. 設定ダイアログに追加
```python
# gui/settings_dialog.py
self.new_option_checkbox = QCheckBox("新しいオプション")
self.new_option_checkbox.setChecked(config.get("new_option", False))
```

3. 設定の保存処理を追加
```python
config["new_option"] = self.new_option_checkbox.isChecked()
```

### 新しい例外クラスの追加

```python
# core/exceptions.py
class NewFeatureError(AATException):
    """新機能に関するエラー"""
    pass
```

### 新しいワーカースレッドの追加

```python
# gui/workers.py
class NewAnalysisWorker(QThread):
    progress = Signal(int)
    result = Signal(dict)
    
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self.data = data
        
    def run(self):
        # 重い処理を実行
        for i in range(100):
            # 処理...
            self.progress.emit(i)
        self.result.emit(analysis_result)
```

### グラフの新しい要素を追加

```python
# gui/main_window.py
def add_custom_annotation(self, ax, x, y, text):
    """グラフにカスタムアノテーションを追加"""
    ax.annotate(
        text,
        xy=(x, y),
        xytext=(x + 0.1, y + 0.1),
        arrowprops=dict(arrowstyle='->', color='red'),
        fontsize=10,
        color='red'
    )
```

---

## トラブルシューティング

### よくある問題と解決方法

#### ImportError: No module named 'PySide6'
```bash
# PySide6の再インストール
pip uninstall PySide6
pip install PySide6
```

#### Signal/Slot接続エラー
```python
# 接続前にオブジェクトの存在を確認
if hasattr(self, 'my_signal'):
    self.my_signal.connect(self.my_slot)
```

#### メモリリーク
```python
# 明示的なクリーンアップ
def closeEvent(self, event):
    # ワーカースレッドを停止
    if self.worker:
        self.worker.quit()
        self.worker.wait()
    event.accept()
```

### デバッグのヒント

1. **ログレベルを上げる**: `AAT_LOG_LEVEL=DEBUG`
2. **ブレークポイントを使う**: VSCodeまたはpdb
3. **メモリプロファイリング**: memory_profiler
4. **スレッドデバッグ**: QThread.currentThread()

---

このガイドは継続的に更新されます。質問や提案がある場合は、GitHubのIssuesで報告してください。
