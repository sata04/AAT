# インストール - Installation

このページでは、AATのインストール方法を説明します。

---

## 📋 システム要件

### 必須要件

- **Python**: 3.10以上
- **オペレーティングシステム**:
  - macOS 13以降（推奨）
  - Windows 10/11
  - Linux（Ubuntu 20.04以降推奨）

### 推奨環境

- メモリ: 4GB以上
- ディスク空き容量: 1GB以上
- ディスプレイ: 1280x720以上の解像度

---

## 🚀 インストール方法

AATは以下の3つの方法でインストール・使用できます:

### 方法1: uv（推奨）

[uv](https://github.com/astral-sh/uv)は高速なPythonパッケージマネージャーです。

```bash
# 1. リポジトリをクローン
git clone https://github.com/sata04/AAT.git
cd AAT

# 2. 仮想環境の作成
uv venv

# 3. 仮想環境の有効化
# macOS/Linux:
source .venv/bin/activate
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 4. 依存関係のインストール
uv pip install -e ".[dev]"
```

### 方法2: pip

標準的なpipを使用する方法です。

```bash
# 1. リポジトリをクローン
git clone https://github.com/sata04/AAT.git
cd AAT

# 2. 仮想環境の作成（推奨）
python -m venv .venv

# 3. 仮想環境の有効化
# macOS/Linux:
source .venv/bin/activate
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 4. 依存関係のインストール
pip install -e ".[dev]"
```

### 方法3: macOSアプリバンドル（macOSのみ）

開発者向けにビルド済みの`.app`バンドルを使用する方法です。詳細は **[[macOSアプリ配布-macOS-App-Distribution]]** をご覧ください。

---

## ✅ インストールの確認

### 1. アプリケーションの起動

```bash
# 仮想環境が有効化されていることを確認
python main.py

# または uvを使用する場合
uv run python main.py
```

メインウィンドウが表示されれば、インストールは成功です！

### 2. バージョンの確認

アプリケーションのメニューバーから「ヘルプ」→「バージョン情報」を選択すると、現在のバージョンが表示されます。

---

## 🔧 開発者向けインストール

開発に参加する場合は、以下の追加ステップを実行してください。

### 1. 開発用依存関係のインストール

```bash
# uvを使用する場合
uv pip install -e ".[dev]"

# pipを使用する場合
pip install -e ".[dev]"
```

これにより、以下のツールがインストールされます:

- `ruff`: リンター・フォーマッター
- `pytest`: テストフレームワーク
- `pytest-cov`: カバレッジ計測
- `pytest-qt`: GUIテスト
- `pre-commit`: Git フック

### 2. pre-commitフックの設定

```bash
uv run pre-commit install
```

これにより、コミット前に自動的にコード品質チェックが実行されます。

### 3. コード品質チェック

```bash
# リントチェック
uv run ruff check .

# フォーマット
uv run ruff format .

# テスト実行
uv run pytest  # pyprojectのaddoptsでカバレッジ出力が有効
```

詳細は **[[開発者ガイド-Developer-Guide]]** をご覧ください。

---

## 🍎 macOSアプリバンドルのビルド

macOS用の`.app`バンドルを自分でビルドする場合:

### 前提条件

- macOS 13以降
- Xcode Command Line Tools (`xcode-select --install`)
- uv がインストール済み

### ビルド手順

```bash
# 1. 仮想環境の作成と有効化
uv venv
source .venv/bin/activate

# 2. ビルド用依存関係のインストール
uv pip install -e ".[build]"

# 3. ビルドスクリプトの実行
python scripts/build_mac_app.py
```

`build/dist/AAT.app` と `build/dmg/AAT.dmg` が生成されます。

詳細は **[[macOSアプリ配布-macOS-App-Distribution]]** をご覧ください。

---

## 🔄 アップグレード

### 最新版への更新

```bash
# リポジトリの更新
git pull origin main

# 依存関係の再インストール
uv pip install -e ".[dev]"  # または pip install -e ".[dev]"
```

### バージョン間の移行

メジャーバージョン更新時は、**[[変更履歴-Changelog]]** でbreaking changesを確認してください。

設定ファイルの形式が変更された場合、AATは初回起動時に自動的に移行します。

---

## 🗑️ アンインストール

### 仮想環境の削除

```bash
# AATディレクトリに移動
cd AAT

# 仮想環境を削除
rm -rf .venv
```

### 設定ファイルの削除

AATの設定ファイルは以下の場所に保存されています:

- **macOS**: `~/Library/Application Support/AAT/`
- **Windows**: `%APPDATA%\AAT\`
- **Linux**: `~/.config/AAT/` または `$XDG_CONFIG_HOME/AAT/`

これらのディレクトリを削除すると、すべての設定がリセットされます。

---

## ❓ トラブルシューティング

### Python バージョンが古い

```bash
# Pythonバージョンの確認
python --version

# 3.10未満の場合は、Pythonをアップグレードしてください
```

### 依存関係のインストールに失敗

```bash
# pipのアップグレード
pip install --upgrade pip

# 依存関係の強制再インストール
pip install -e ".[dev]" --force-reinstall
```

### macOSでの権限エラー

```bash
# Xcode Command Line Toolsのインストール
xcode-select --install
```

### その他の問題

**[[トラブルシューティング-Troubleshooting]]** ページをご覧ください。

---

## 🚀 次のステップ

インストールが完了したら:

1. **[[使い方-Usage]]** - 基本的な使い方を学ぶ
2. **[[GUI操作ガイド-GUI-Guide]]** - UIの詳細を確認
3. **[[使用例-Examples]]** - 実際の使用例を見る

[[Home]] に戻る
