# AAT テストガイド

## 目次

1. [概要](#概要)
2. [テスト戦略](#テスト戦略)
3. [テスト環境のセットアップ](#テスト環境のセットアップ)
4. [ユニットテスト](#ユニットテスト)
5. [統合テスト](#統合テスト)
6. [GUIテスト](#guiテスト)
7. [パフォーマンステスト](#パフォーマンステスト)
8. [テストデータ](#テストデータ)
9. [継続的インテグレーション](#継続的インテグレーション)
10. [テストのベストプラクティス](#テストのベストプラクティス)

---

## 概要

このガイドでは、AATプロジェクトのテスト戦略、テストケースの作成方法、およびテストの実行方法について説明します。品質の高いソフトウェアを維持するため、包括的なテストカバレッジを目指します。

**注意**: テストは `tests/` ディレクトリに実装されています。このドキュメントは、現在のテスト構成と実行方法について説明します。

### テストの重要性

- **バグの早期発見**: 開発段階でバグを発見し、修正コストを削減
- **リファクタリングの安全性**: テストがあることで安心してコードを改善
- **ドキュメントとしての役割**: テストコードが仕様の実例となる
- **品質保証**: リリース前の品質を保証

---

## テスト戦略

### テストピラミッド

```
          /\
         /  \     E2Eテスト (5%)
        /    \    - エンドツーエンドシナリオ
       /──────\
      /        \  統合テスト (25%)
     /          \ - モジュール間の連携
    /────────────\
   /              \ ユニットテスト (70%)
  /________________\ - 個別関数・クラスのテスト
```

### テストカバレッジ目標

| テストタイプ | カバレッジ目標 | 現状 | 優先度 | 実装状況 |
|------------|--------------|------|--------|----------|
| ユニットテスト | 80%以上 | 実装済 | 高 | `tests/` 直下に配置 |
| 統合テスト | 60%以上 | 一部実装 | 中 | ユニットテストと併用 |
| GUIテスト | 主要機能 | 実装済 | 中 | `tests/gui/` に配置 |
| E2Eテスト | クリティカルパス | 未実装 | 低 | 将来実装 |

---

## テスト環境のセットアップ

### 必要なパッケージのインストール

```bash
# 開発依存関係をインストール
pip install -e ".[dev]"

# または個別にインストール
pip install pytest pytest-cov pytest-qt pytest-mock
```

### テストディレクトリ構造（提案）

**注意**: 以下は提案されるテストディレクトリ構造です。実装時に作成してください。

tests/
├── __init__.py
├── conftest.py              # 共通のフィクスチャ
├── test_data_processor.py   # データ処理のユニットテスト
├── test_statistics.py       # 統計計算のユニットテスト
├── test_cache_manager.py    # キャッシュ管理のユニットテスト
├── test_export.py          # エクスポート機能のユニットテスト
├── test_config.py          # 設定管理のユニットテスト
├── test_workers.py         # ワーカースレッドのテスト
├── gui/                     # GUIテスト
│   ├── __init__.py
│   └── test_main_window_smoke.py # メインウィンドウのスモークテスト
└── fixtures/               # テストデータ（必要に応じて作成）

### 共通フィクスチャの設定

**注意**: 以下のコード例は、将来のテスト実装時の参考例です。現在、testsディレクトリおよびテストコードは実装されていません。

```python
# tests/conftest.py （実装例）
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

@pytest.fixture
def sample_config():
    """テスト用の標準設定"""
    return {
        "sampling_rate": 1000,
        "gravity_constant": 9.797578,
        "window_size": 0.1,
        "acceleration_threshold": 1.0,
        "end_gravity_level": 8,
        "use_cache": False  # テストではキャッシュを無効化
    }

@pytest.fixture
def sample_data():
    """テスト用のサンプルデータ"""
    time = np.arange(0, 10, 0.001)  # 10秒間のデータ
    acceleration = np.random.normal(0, 0.1, len(time))

    # 同期点を追加（t=1秒）
    acceleration[1000:1003] = 2.0

    return pd.DataFrame({
        'Time (s)': time,
        'Acceleration 1 (m/s²)': acceleration,
        'Acceleration 2 (m/s²)': acceleration * 0.8
    })

@pytest.fixture
def temp_csv_file(tmp_path, sample_data):
    """一時的なCSVファイルを作成"""
    file_path = tmp_path / "test_data.csv"
    sample_data.to_csv(file_path, index=False)
    return str(file_path)
```

---

## ユニットテスト

**重要**: 以下のセクションのすべてのテストコードは実装例です。実際のテストファイルはまだ作成されていません。

### データ処理モジュールのテスト

```python
# tests/unit/test_data_processor.py （実装例）
import pytest
import pandas as pd
from core.data_processor import detect_columns, load_and_process_data, filter_data
from core.exceptions import ColumnNotFoundError, SyncPointNotFoundError

class TestDetectColumns:
    def test_detect_columns_standard_format(self, temp_csv_file):
        """標準的な列名の検出テスト"""
        time_cols, acc_cols = detect_columns(temp_csv_file)

        assert len(time_cols) > 0
        assert "Time (s)" in time_cols
        assert len(acc_cols) >= 2

    def test_detect_columns_japanese_format(self, tmp_path):
        """日本語列名の検出テスト"""
        df = pd.DataFrame({
            '時間(s)': [0, 1, 2],
            '加速度1(m/s²)': [0.1, 0.2, 0.3],
            '加速度2(m/s²)': [0.1, 0.2, 0.3]
        })
        file_path = tmp_path / "japanese.csv"
        df.to_csv(file_path, index=False)

        time_cols, acc_cols = detect_columns(str(file_path))
        assert '時間(s)' in time_cols
        assert '加速度1(m/s²)' in acc_cols

class TestLoadAndProcessData:
    def test_successful_load(self, temp_csv_file, sample_config):
        """正常なデータ読み込みテスト"""
        sample_config.update({
            'time_column': 'Time (s)',
            'acceleration_column_inner_capsule': 'Acceleration 1 (m/s²)',
            'acceleration_column_drag_shield': 'Acceleration 2 (m/s²)'
        })

        result = load_and_process_data(temp_csv_file, sample_config)
        time, gl_ic, gl_ds, adj_time = result

        assert len(time) == len(gl_ic) == len(gl_ds) == len(adj_time)
        assert time[0] == 0  # 時間は0から開始

    def test_missing_column_error(self, temp_csv_file, sample_config):
        """存在しない列指定時のエラーテスト"""
        sample_config['time_column'] = 'NonExistentColumn'

        with pytest.raises(ColumnNotFoundError):
            load_and_process_data(temp_csv_file, sample_config)

    def test_sync_point_detection(self, temp_csv_file, sample_config):
        """同期点検出のテスト"""
        sample_config.update({
            'time_column': 'Time (s)',
            'acceleration_column_inner_capsule': 'Acceleration 1 (m/s²)',
            'acceleration_column_drag_shield': 'Acceleration 2 (m/s²)',
            'acceleration_threshold': 1.5
        })

        _, _, _, adj_time = load_and_process_data(temp_csv_file, sample_config)

        # 調整後の時間は同期点で0になる
        assert adj_time.min() < 0  # 同期前の時間は負
        assert 0 in adj_time.values or abs(adj_time[adj_time >= 0].iloc[0]) < 0.001
```

### 統計モジュールのテスト

```python
# tests/unit/test_statistics.py
import pytest
import pandas as pd
import numpy as np
from core.statistics import calculate_statistics, calculate_range_statistics

class TestCalculateStatistics:
    def test_normal_calculation(self):
        """正常な統計計算のテスト"""
        # 10秒間のデータ、標準偏差が変化するように設定
        time = pd.Series(np.arange(0, 10, 0.001))
        gravity_level = pd.Series(np.concatenate([
            np.random.normal(0, 0.5, 5000),   # 高ノイズ
            np.random.normal(0, 0.1, 5000)    # 低ノイズ
        ]))

        config = {"window_size": 0.1, "sampling_rate": 1000}
        mean_abs, start_time, min_std = calculate_statistics(
            gravity_level, time, config
        )

        assert mean_abs is not None
        assert 5.0 <= start_time <= 9.9  # 低ノイズ区間で検出されるはず
        assert min_std < 0.2  # 低い標準偏差

    def test_insufficient_data(self):
        """データ不足時のテスト"""
        time = pd.Series([0, 0.001])  # 2点のみ
        gravity_level = pd.Series([0.1, 0.2])
        config = {"window_size": 0.1, "sampling_rate": 1000}

        result = calculate_statistics(gravity_level, time, config)
        assert result == (None, None, None)

    def test_mismatched_lengths(self):
        """データ長不一致時のエラーテスト"""
        time = pd.Series([0, 1, 2])
        gravity_level = pd.Series([0.1, 0.2])  # 長さが異なる
        config = {"window_size": 0.1, "sampling_rate": 1000}

        with pytest.raises(ValueError):
            calculate_statistics(gravity_level, time, config)

class TestCalculateRangeStatistics:
    def test_comprehensive_statistics(self):
        """範囲統計の包括的テスト"""
        data = np.array([1, -2, 3, -4, 5])
        stats = calculate_range_statistics(data)

        assert stats['mean'] == pytest.approx(0.6)
        assert stats['abs_mean'] == pytest.approx(3.0)
        assert stats['std'] == pytest.approx(3.13, rel=0.01)
        assert stats['min'] == -4
        assert stats['max'] == 5
        assert stats['range'] == 9
        assert stats['count'] == 5

    def test_empty_array(self):
        """空配列のテスト"""
        stats = calculate_range_statistics(np.array([]))

        for key in ['mean', 'abs_mean', 'std', 'min', 'max', 'range']:
            assert stats[key] is None
        assert stats['count'] == 0
```

### キャッシュマネージャーのテスト

```python
# tests/unit/test_cache_manager.py
import pytest
from pathlib import Path
from core.cache_manager import (
    generate_cache_id, get_cache_path, save_to_cache,
    load_from_cache, has_valid_cache, delete_cache
)

class TestCacheManager:
    def test_cache_id_generation(self):
        """キャッシュID生成のテスト"""
        config1 = {"param1": 1, "param2": "test"}
        config2 = {"param1": 1, "param2": "test"}
        config3 = {"param1": 2, "param2": "test"}

        id1 = generate_cache_id("file.csv", config1)
        id2 = generate_cache_id("file.csv", config2)
        id3 = generate_cache_id("file.csv", config3)

        assert id1 == id2  # 同じ設定なら同じID
        assert id1 != id3  # 異なる設定なら異なるID
        assert len(id1) == 16  # 16文字のハッシュ

    def test_cache_save_and_load(self, tmp_path):
        """キャッシュの保存と読み込みテスト"""
        file_path = str(tmp_path / "data.csv")
        cache_id = "test_cache_id"
        test_data = {
            "data": [1, 2, 3],
            "metadata": {"version": "1.0"}
        }
        config = {"app_version": "9.1.0"}

        # 保存
        success = save_to_cache(test_data, file_path, cache_id, config)
        assert success

        # 読み込み
        loaded_data = load_from_cache(file_path, cache_id)
        assert loaded_data is not None
        assert loaded_data["data"] == [1, 2, 3]
        assert loaded_data["metadata"]["version"] == "1.0"

    def test_cache_deletion(self, tmp_path):
        """キャッシュ削除のテスト"""
        file_path = str(tmp_path / "data.csv")
        cache_id = "test_cache_id"
        test_data = {"data": "test"}
        config = {"app_version": "9.1.0"}

        # キャッシュを作成
        save_to_cache(test_data, file_path, cache_id, config)
        assert has_valid_cache(file_path, config)[0]

        # キャッシュを削除
        success = delete_cache(file_path, cache_id)
        assert success
        assert not has_valid_cache(file_path, config)[0]
```

---

## 統合テスト

### データパイプライン統合テスト

```python
# tests/integration/test_data_pipeline.py
import pytest
from core.data_processor import load_and_process_data, filter_data
from core.statistics import calculate_statistics
from core.export import export_data

class TestDataPipeline:
    def test_full_pipeline(self, temp_csv_file, sample_config, tmp_path):
        """データ処理の全パイプラインテスト"""
        # 設定
        sample_config.update({
            'time_column': 'Time (s)',
            'acceleration_column_inner_capsule': 'Acceleration 1 (m/s²)',
            'acceleration_column_drag_shield': 'Acceleration 2 (m/s²)'
        })

        # 1. データ読み込みと処理
        time, gl_ic, gl_ds, adj_time = load_and_process_data(
            temp_csv_file, sample_config
        )

        # 2. フィルタリング
        f_time, f_gl_ic, f_gl_ds, f_adj_time, end_idx = filter_data(
            time, gl_ic, gl_ds, adj_time, sample_config
        )

        # 3. 統計計算
        stats_ic = calculate_statistics(f_gl_ic, f_time, sample_config)
        stats_ds = calculate_statistics(f_gl_ds, f_time, sample_config)

        # 4. エクスポート
        output_path = export_data(
            time, gl_ic, gl_ds, adj_time,
            temp_csv_file, sample_config,
            stats_ic[0], stats_ic[1], stats_ic[2],
            stats_ds[0], stats_ds[1], stats_ds[2],
            f_time, end_idx
        )

        # 検証
        assert Path(output_path).exists()
        assert output_path.endswith('.xlsx')
```

### キャッシュ統合テスト

```python
# tests/integration/test_cache_integration.py
import pytest
import time
from core.data_processor import load_and_process_data
from core.cache_manager import has_valid_cache

class TestCacheIntegration:
    def test_cache_performance(self, temp_csv_file, sample_config):
        """キャッシュによるパフォーマンス向上テスト"""
        sample_config.update({
            'time_column': 'Time (s)',
            'acceleration_column_inner_capsule': 'Acceleration 1 (m/s²)',
            'acceleration_column_drag_shield': 'Acceleration 2 (m/s²)',
            'use_cache': True
        })

        # 初回実行（キャッシュなし）
        start = time.time()
        result1 = load_and_process_data(temp_csv_file, sample_config)
        first_run_time = time.time() - start

        # キャッシュが作成されたことを確認
        assert has_valid_cache(temp_csv_file, sample_config)[0]

        # 2回目実行（キャッシュあり）
        start = time.time()
        result2 = load_and_process_data(temp_csv_file, sample_config)
        second_run_time = time.time() - start

        # キャッシュの方が高速であることを確認
        assert second_run_time < first_run_time * 0.5

        # 結果が同一であることを確認
        for i in range(4):
            assert result1[i].equals(result2[i])
```

---

## GUIテスト

### メインウィンドウのテスト

```python
# tests/gui/test_main_window.py
import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from gui.main_window import MainWindow

@pytest.fixture
def main_window(qtbot):
    """メインウィンドウのフィクスチャ"""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window

class TestMainWindow:
    def test_initial_state(self, main_window):
        """初期状態のテスト"""
        assert main_window.windowTitle() == "AAT - Acceleration Analysis Tool"
        assert main_window.select_file_button.isEnabled()
        assert main_window.g_quality_button.isEnabled() is False

    def test_file_selection_button(self, main_window, qtbot, mocker):
        """ファイル選択ボタンのテスト"""
        # ファイルダイアログをモック
        mocker.patch(
            'PySide6.QtWidgets.QFileDialog.getOpenFileNames',
            return_value=(["test.csv"], "")
        )

        # ボタンクリック
        qtbot.mouseClick(
            main_window.select_file_button,
            Qt.MouseButton.LeftButton
        )

        # ファイル処理が開始されることを確認
        assert main_window.current_file == "test.csv"

    def test_settings_dialog(self, main_window, qtbot):
        """設定ダイアログのテスト"""
        # 設定ボタンをクリック
        qtbot.mouseClick(
            main_window.settings_button,
            Qt.MouseButton.LeftButton
        )

        # ダイアログが表示されることを確認
        assert main_window.settings_dialog is not None
        assert main_window.settings_dialog.isVisible()

    def test_graph_interaction(self, main_window, qtbot):
        """グラフインタラクションのテスト"""
        # サンプルデータを設定
        import numpy as np
        time_data = np.arange(0, 10, 0.1)
        gravity_data = np.sin(time_data)

        main_window.plot_gravity_levels(
            time_data, gravity_data, gravity_data * 0.8,
            time_data, None, None, None
        )

        # グラフが描画されたことを確認
        assert len(main_window.ax1.lines) > 0
        assert len(main_window.ax2.lines) > 0
```

### ワーカースレッドのテスト

```python
# tests/gui/test_workers.py
import pytest
from PySide6.QtCore import QEventLoop
from gui.workers import GQualityWorker
import pandas as pd
import numpy as np

class TestGQualityWorker:
    def test_worker_execution(self, qtbot):
        """G-qualityワーカーの実行テスト"""
        # テストデータ
        time = pd.Series(np.arange(0, 5, 0.001))
        gl_ic = pd.Series(np.random.normal(0, 0.1, len(time)))
        gl_ds = pd.Series(np.random.normal(0, 0.1, len(time)))
        config = {
            'g_quality_start': 0.1,
            'g_quality_end': 0.5,
            'g_quality_step': 0.1,
            'sampling_rate': 1000
        }

        # ワーカー作成
        worker = GQualityWorker(time, gl_ic, gl_ds, config)

        # シグナル監視
        with qtbot.waitSignals([worker.finished, worker.result], timeout=5000):
            worker.start()

        # 結果の検証
        assert hasattr(worker, 'g_quality_data')
        assert 'window_sizes' in worker.g_quality_data
        assert len(worker.g_quality_data['window_sizes']) == 5

### テーマ切り替えのテスト

```python
# tests/gui/test_theme.py
def test_theme_switching(main_window, qtbot):
    """テーマ切り替えのテスト"""
    from gui.styles import ThemeType

    # ダークモードに切り替え
    main_window.dark_theme_action.trigger()
    assert main_window.current_theme_type == ThemeType.DARK

    # ライトモードに切り替え
    main_window.light_theme_action.trigger()
    assert main_window.current_theme_type == ThemeType.LIGHT

    # システムデフォルトに切り替え
    main_window.system_theme_action.trigger()
    assert main_window.current_theme_type == ThemeType.SYSTEM
```
```

---

## パフォーマンステスト

### 大容量ファイルのテスト

```python
# tests/performance/test_large_files.py
import pytest
import numpy as np
import pandas as pd
import time
from core.data_processor import load_and_process_data

class TestPerformance:
    @pytest.mark.slow
    def test_large_file_processing(self, tmp_path, sample_config):
        """大容量ファイル処理のパフォーマンステスト"""
        # 100MBのテストデータ生成
        n_points = 10_000_000  # 1000万点
        time_data = np.arange(0, n_points / 1000, 0.001)
        acc_data = np.random.normal(0, 0.1, n_points)

        df = pd.DataFrame({
            'Time (s)': time_data,
            'Acceleration 1 (m/s²)': acc_data,
            'Acceleration 2 (m/s²)': acc_data * 0.8
        })

        file_path = tmp_path / "large_data.csv"
        df.to_csv(file_path, index=False)

        sample_config.update({
            'time_column': 'Time (s)',
            'acceleration_column_inner_capsule': 'Acceleration 1 (m/s²)',
            'acceleration_column_drag_shield': 'Acceleration 2 (m/s²)'
        })

        # 処理時間測定
        start_time = time.time()
        result = load_and_process_data(str(file_path), sample_config)
        processing_time = time.time() - start_time

        # パフォーマンス基準: 100MBを30秒以内で処理
        assert processing_time < 30
        assert result[0] is not None

    @pytest.mark.slow
    def test_memory_usage(self, tmp_path, sample_config):
        """メモリ使用量のテスト"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 処理実行
        # ... (大容量ファイル処理)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # メモリ使用量が2GB以下であることを確認
        assert memory_increase < 2048
```

---

## テストデータ

### テストフィクスチャの作成

```python
# tests/fixtures/create_test_data.py
import pandas as pd
import numpy as np

def create_sample_data():
    """標準的なテストデータの作成"""
    time = np.arange(0, 10, 0.001)

    # 同期点を含む加速度データ
    acc = np.random.normal(0, 0.05, len(time))
    acc[1000:1005] = 2.0  # t=1秒に同期点

    # 微小重力区間（t=3-8秒）
    acc[3000:8000] = np.random.normal(0, 0.01, 5000)

    df = pd.DataFrame({
        'データセット1:時間(s)': time,
        'データセット1:Z-axis acceleration 1(m/s²)': acc,
        'データセット1:Z-axis acceleration 2(m/s²)': acc * 0.8
    })

    df.to_csv('tests/fixtures/sample_data.csv', index=False)

def create_invalid_data():
    """異常系テスト用データの作成"""
    # 列名が不正
    df1 = pd.DataFrame({
        'Column1': [1, 2, 3],
        'Column2': [4, 5, 6]
    })
    df1.to_csv('tests/fixtures/invalid_columns.csv', index=False)

    # データが不足
    df2 = pd.DataFrame({
        'Time (s)': [0, 0.001],
        'Acceleration (m/s²)': [0.1, 0.2]
    })
    df2.to_csv('tests/fixtures/insufficient_data.csv', index=False)

if __name__ == "__main__":
    create_sample_data()
    create_invalid_data()
```

---

## 継続的インテグレーション

### GitHub Actions設定

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run tests with coverage
      run: |
        pytest --cov=core --cov=gui --cov-report=xml --cov-report=term

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

### ローカルでのテスト実行

**注意**: 以下のコマンドでテストを実行できます。

```bash
# すべてのテストを実行（テスト実装後）
pytest

# 特定のディレクトリのテストを実行
pytest tests/unit/

# 特定のファイルのテストを実行
pytest tests/test_statistics.py

# 特定のテストケースを実行
pytest tests/test_statistics.py::TestCalculateStatistics::test_normal_calculation

# カバレッジ付きで実行
pytest --cov=core --cov=gui --cov-report=html

# 遅いテストをスキップ
pytest -m "not slow"

# 並列実行（pytest-xdistが必要）
pytest -n auto

# デバッグモードで実行
pytest -vv --tb=short
```

---

## テストのベストプラクティス

### 1. テストの命名規則

```python
# 良い例
def test_calculate_statistics_with_valid_data():
    """有効なデータでの統計計算が正しく動作すること"""
    pass

def test_load_csv_raises_error_on_missing_file():
    """存在しないファイルでエラーが発生すること"""
    pass

# 悪い例
def test1():  # 何をテストしているか不明
    pass
```

### 2. Arrange-Act-Assert パターン

```python
def test_example():
    # Arrange: テストの準備
    data = create_test_data()
    config = get_test_config()

    # Act: テスト対象の実行
    result = process_data(data, config)

    # Assert: 結果の検証
    assert result is not None
    assert len(result) == expected_length
```

### 3. フィクスチャの活用

```python
@pytest.fixture(scope="session")
def expensive_resource():
    """高コストなリソースはセッションスコープで共有"""
    resource = create_expensive_resource()
    yield resource
    cleanup_resource(resource)

@pytest.fixture
def mock_file_dialog(mocker):
    """ファイルダイアログのモック"""
    return mocker.patch('PySide6.QtWidgets.QFileDialog.getOpenFileName')
```

### 4. パラメータ化テスト

```python
@pytest.mark.parametrize("window_size,expected_samples", [
    (0.1, 100),
    (0.5, 500),
    (1.0, 1000),
])
def test_window_size_calculation(window_size, expected_samples):
    """異なるウィンドウサイズでのサンプル数計算"""
    sampling_rate = 1000
    samples = int(window_size * sampling_rate)
    assert samples == expected_samples
```

### 5. テストの独立性

```python
# 良い例: 各テストが独立
def test_cache_save(temp_cache_dir):
    # temp_cache_dirは各テストで新規作成される
    save_to_cache(data, temp_cache_dir)
    assert cache_exists(temp_cache_dir)

# 悪い例: 前のテストに依存
def test_cache_load():
    # 前のテストでキャッシュが作成されていることを前提
    data = load_from_cache()  # 危険！
```

### 6. エラーケースのテスト

```python
def test_error_cases():
    """エラーケースを網羅的にテスト"""
    # 境界値
    with pytest.raises(ValueError):
        process_data([])  # 空のデータ

    # 異常値
    with pytest.raises(ValueError):
        process_data(None)  # Null

    # 型エラー
    with pytest.raises(TypeError):
        process_data("invalid")  # 不正な型
```

### 7. モックの適切な使用

```python
def test_with_mock(mocker):
    """外部依存をモック化"""
    # ファイルシステムのモック
    mock_exists = mocker.patch('pathlib.Path.exists')
    mock_exists.return_value = True

    # 時間のモック
    mock_time = mocker.patch('time.time')
    mock_time.return_value = 1234567890.0

    # テスト実行
    result = function_under_test()

    # モックが呼ばれたことを確認
    mock_exists.assert_called_once()
```

---

このテストガイドは、AATプロジェクトの品質を維持し、継続的な改善を支援するために作成されました。新しいテストケースやテスト手法の追加により、常に更新されることを想定しています。

最終更新日: 2024年12月
