# 🚀 AAT (Acceleration Analysis Tool) v9.1.0

> 微小重力環境の実験データを簡単に分析・可視化するためのデスクトップアプリケーション

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)

## 📖 概要

AATは、宇宙環境での微小重力実験データを分析するための専用ツールです。CSVファイルの加速度データを読み込んで、重力レベルの計算・可視化・統計分析を行うことができます。直感的なGUIで誰でも簡単に使用できます。

## ✨ 主な特徴

- 📊 **簡単データ分析**: CSVファイルをドラッグ&ドロップするだけ
- 📈 **リアルタイム可視化**: 美しいグラフでデータを即座に表示
- 🔍 **詳細統計分析**: G-quality評価による高精度な微小重力環境評価
- 💾 **自動データ保存**: Excel形式での結果出力とグラフ画像の自動保存
- ⚡ **高速処理**: キャッシュ機能による高速な再処理
- 🖱️ **インタラクティブ**: グラフ上でのマウス操作による範囲選択分析

## 🚀 クイックスタート

### 1. 必要な環境

- **Python 3.7以上**
- **オペレーティングシステム**: Windows、macOS、Linux

### 2. インストール

```bash
# リポジトリをクローン
git clone https://github.com/sata04/AAT.git
cd AAT

# 必要なライブラリをインストール
pip install -r requirements.txt
```

### 3. アプリケーションの起動

```bash
python main.py
```

### 4. 最初のデータ分析

1. 「**CSVファイルを選択**」ボタンをクリック
2. 分析したいCSVファイルを選択
3. データが自動的に処理され、グラフが表示されます！

## 📖 基本的な使い方

### ステップ1: データファイルの選択
- 加速度データが含まれたCSVファイルを準備
- アプリで「CSVファイルを選択」をクリック
- 複数ファイルの同時選択も可能

### ステップ2: データの確認
- グラフが自動表示され、Inner CapsuleとDrag Shieldの重力レベルが表示
- 下部のテーブルで統計情報を確認
- 処理状況がリアルタイムで表示

### ステップ3: 結果の保存
- データは自動的にExcel形式で保存
- グラフ画像も同時に保存
- `results_AAT`フォルダに整理して保存

## ⚙️ 基本設定

設定ダイアログで以下のパラメータを調整できます：

| 設定項目 | 説明 | デフォルト値 |
|---------|------|-------------|
| サンプリングレート | データの周波数 | 1000 Hz |
| 重力定数 | 基準重力値 | 9.79758 m/s² |
| ウィンドウサイズ | 分析の時間窓 | 0.1秒 |
| キャッシュ使用 | 高速処理の有効化 | ON |

## 🔧 詳細機能

<details>
<summary><strong>🎯 G-quality評価モード</strong></summary>

微小重力環境の品質を詳細に評価する高度な分析機能：

- **多段階ウィンドウ分析**: 0.1秒から1.0秒まで異なるサイズの時間窓で分析
- **最適化された処理**: バックグラウンドでの非同期処理により、UIの応答性を維持
- **比較分析**: Inner CapsuleとDrag Shieldの両方を独立して評価
- **自動実行**: ファイル読み込み時の自動評価オプション

使用方法：
1. 「G-quality評価モード」ボタンをクリック
2. 進捗バーで処理状況を確認
3. 結果がグラフとExcelで自動保存
</details>

<details>
<summary><strong>🖱️ インタラクティブ分析</strong></summary>

グラフ上での直感的な操作機能：

- **範囲選択**: マウスドラッグで時間範囲を選択
- **リアルタイム統計**: 選択範囲の詳細統計を即座に表示
- **ビジュアルフィードバック**: 選択範囲のハイライト表示
- **データ比較**: 複数データセットの同時表示と比較

操作方法：
1. グラフ上でマウスをドラッグして範囲選択
2. 統計情報ダイアログが自動表示
3. 平均値、標準偏差などの詳細データを確認
</details>

<details>
<summary><strong>💾 キャッシュシステム</strong></summary>

処理済みデータの高速再利用機能：

- **自動キャッシュ**: 処理結果を自動的に保存
- **整合性チェック**: ファイル変更時の自動再処理
- **バージョン管理**: アプリケーション更新時の自動キャッシュ更新
- **効率的な保存**: pickle形式とHDF5形式の使い分け
</details>

## 📁 出力ファイル構造

```
<元のCSVファイルのディレクトリ>/
└── results_AAT/
    ├── 📊 <ファイル名>.xlsx         # 総合分析結果
    │   ├── Gravity Level Data      # 重力レベルデータ
    │   ├── Gravity Level Statistics # 統計情報
    │   ├── Acceleration Data       # 元の加速度データ
    │   └── G-quality Analysis      # G-quality分析結果
    ├── 📁 cache/                   # 高速処理用キャッシュ
    │   ├── *.pickle               # 処理済みデータ
    │   └── *_raw.h5               # 生加速度データ
    └── 📁 graphs/                  # グラフ画像
        ├── <ファイル名>_gl.png    # 重力レベルグラフ
        └── <ファイル名>_gq.png    # G-quality分析グラフ
```

## ❓ トラブルシューティング

### よくある問題と解決法

**Q: アプリケーションが起動しない**
```bash
# 依存関係を再インストール
pip install -r requirements.txt --force-reinstall

# Python バージョンを確認
python --version  # 3.7以上が必要
```

**Q: CSVファイルが読み込めない**
- ファイル形式を確認（UTF-8エンコーディング推奨）
- 必要な列（時間、加速度）が含まれているか確認
- 列選択ダイアログで手動指定を試す

**Q: 処理が遅い**
- キャッシュ機能を有効にする
- 不要なバックグラウンドアプリケーションを終了
- ファイルサイズが大きすぎる場合は分割を検討

**Q: macOSでの警告メッセージ**
- 機能には影響しません
- デバッグモードで詳細確認: `AAT_DEBUG=1 python main.py`

### サポートが必要な場合

🐛 [GitHub Issues](https://github.com/sata04/AAT/issues)でバグ報告・機能リクエストを受け付けています

## 📚 開発者向け情報

<details>
<summary><strong>🏗️ アーキテクチャ</strong></summary>

### プロジェクト構造
```
AAT/
├── main.py                     # エントリーポイント
├── config.json                 # 設定ファイル
├── core/                      # コア処理モジュール
│   ├── data_processor.py      # データ処理
│   ├── statistics.py          # 統計分析
│   ├── cache_manager.py       # キャッシュ管理
│   ├── export.py             # エクスポート機能
│   ├── config.py             # 設定管理
│   └── logger.py             # ログ機能
└── gui/                      # ユーザーインターフェース
    ├── main_window.py        # メインウィンドウ
    ├── workers.py            # バックグラウンド処理
    ├── settings_dialog.py    # 設定ダイアログ
    └── column_selector_dialog.py  # 列選択ダイアログ
```

### 設計原則
- **関心の分離**: コア処理とGUIの完全分離
- **非同期処理**: QThreadによるバックグラウンド処理
- **キャッシュ戦略**: インテリジェントな処理結果再利用
- **設定管理**: JSONベースの柔軟な設定システム
</details>

<details>
<summary><strong>🔧 開発環境設定</strong></summary>

### 開発用依存関係
```bash
pip install -r requirements.txt
```

### デバッグモード
```bash
# macOS
AAT_DEBUG=1 python main.py

# Windows
set AAT_DEBUG=1 && python main.py
```

### テスト実行
```bash
# 基本テスト
python -m pytest tests/

# カバレッジ付き
python -m pytest tests/ --cov=core --cov=gui
```
</details>

## 📝 更新履歴

### v9.1.0 (2024年12月)
- 🔧 同期点検出アルゴリズムの改善
- 📊 時間軸調整の精度向上
- 🗂️ 出力ディレクトリ管理の強化
- 🎨 UIレイアウトの改善
- 🔗 matplotlib互換性の向上

### v9.0.0 (2024年11月)
- ⚡ バックグラウンド処理によるUIの応答性向上
- 🖱️ グラフ上での範囲選択機能追加
- 📊 リアルタイム進捗表示の強化
- 💾 キャッシュシステムの最適化
- 🛡️ エラーハンドリングの強化

## 📄 ライセンス

このプロジェクトは [Apache License 2.0](LICENSE.md) の下で公開されています。

## 📞 サポート・コンタクト

- 🐛 **バグ報告**: [GitHub Issues](https://github.com/sata04/AAT/issues)
- 💡 **機能リクエスト**: [GitHub Issues](https://github.com/sata04/AAT/issues)
- 📧 **その他のお問い合わせ**: GitHubのissueトラッカーをご利用ください

---

<div align="center">

**AATを使用して素晴らしい微小重力実験データ分析を！** 🚀

Made with ❤️ for scientific research

</div>
