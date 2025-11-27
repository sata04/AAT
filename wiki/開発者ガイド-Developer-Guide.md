# 開発者ガイド - Developer Guide

このページでは、AATの開発に参加するための情報を提供します。

> [!NOTE]
> 詳細情報は [docs/developer-guide.md](https://github.com/sata04/AAT/blob/main/docs/developer-guide.md) をご覧ください。

---

## 🛠️ 開発環境のセットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/sata04/AAT.git
cd AAT
```

### 2. 仮想環境の作成

```bash
# uvを使用（推奨）
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# または標準のvenv
python -m venv .venv
source .venv/bin/activate
```

### 3. 開発用依存関係のインストール

```bash
uv pip install -e ".[dev]"
# または: pip install -e ".[dev]"
```

これにより、以下がインストールされます:
- Ruff (リンター/フォーマッター)
- pytest (テストフレームワーク)
- pytest-cov (カバレッジ)
- pytest-qt (GUIテスト)
- pre-commit (Gitフック)

---

## 🧪 テストの実行

```bash
# 全テストを実行（pyprojectのaddoptsで -v/--cov が付与されています）
uv run pytest

# 特定のテストのみ実行
uv run pytest tests/test_data_processor.py

# GUIテストを除外
uv run pytest -m "not gui"
```

詳細は **[docs/testing-guide.md](https://github.com/sata04/AAT/blob/main/docs/testing-guide.md)** を参照してください。

---

## 🎨 コード品質チェック

### Ruffによるリント・フォーマット

```bash
# リントチェック
uv run ruff check .

# 自動修正
uv run ruff check . --fix

# フォーマット
uv run ruff format .
```

### pre-commitフックの設定

```bash
uv run pre-commit install

# 手動実行
uv run pre-commit run --all-files
```

---

## 📝 コーディング規約

### Pythonスタイル

- **PEP 8** に準拠
- **行の長さ**: 最大120文字
- **インデント**: スペース4つ
- **クォート**: ダブルクォート `"` を使用

### 命名規則

- **関数/変数**: `snake_case`
- **クラス**: `PascalCase`
- **定数**: `UPPER_SNAKE_CASE`
- **プライベート**: `_leading_underscore`

### ドキュメントstring

すべての public 関数にdocstringを記載:

```python
def calculate_statistics(gravity_level: pd.Series, time: pd.Series, config: dict):
    \"\"\"
    重力レベルデータの統計情報を計算する

    Args:
        gravity_level: 重力レベルデータ
        time: 時間データ
        config: 設定パラメータ

    Returns:
        (平均G, 開始時間, 標準偏差) のタプル
    \"\"\"
```

---

## 🏗️ アーキテクチャガイドライン

### モジュール分離

- **`core/`**: ビジネスロジック（GUI非依存）
- **`gui/`**: UIコンポーネント（PySide6）

### 非同期処理

長時間処理は`QThread`を使用:

```python
from PySide6.QtCore import QThread, Signal

class MyWorker(QThread):
    progress = Signal(int)
    finished = Signal(dict)

    def run(self):
        # 処理
        self.progress.emit(50)
        result = process_data()
        self.finished.emit(result)
```

---

## 🔧 デバッグ

### デバッグモード

```bash
AAT_DEBUG=1 uv run python main.py
```

### ログレベル

```bash
AAT_LOG_LEVEL=DEBUG uv run python main.py
```

ログは標準出力に出力されます（専用のログファイルはありません）。問題報告時はターミナル出力を共有してください。

---

## 📦 ビルド

### macOSアプリバンドル

詳細は **[[macOSアプリ配布-macOS-App-Distribution]]** を参照してください。

```bash
uv pip install -e ".[build]"
python scripts/build_mac_app.py
```

---

## 🤝 貢献方法

### 1. Issueの作成

バグ報告や機能リクエストは [GitHub Issues](https://github.com/sata04/AAT/issues) で。

### 2. Pull Requestの作成

1. フォークする
2. ブランチを作成: `git checkout -b feature/my-feature`
3. 変更をコミット: `git commit -am 'Add my feature'`
4. プッシュ: `git push origin feature/my-feature`
5. PRを作成

### 3. レビュー

- テストが通ること
- コード品質チェックをパスすること
- ドキュメントが更新されていること

詳細は [CONTRIBUTING.md](../CONTRIBUTING.md) を参照してください。

---

## 🚀 次のステップ

- **[[プロジェクト構造-Project-Structure]]** - コード構成の理解
- **[[APIリファレンス-API-Reference]]** - APIの詳細
- **[Testing Guide](https://github.com/sata04/AAT/blob/main/docs/testing-guide.md)** - テスト戦略
