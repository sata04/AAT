# 🚀 AAT (Acceleration Analysis Tool) Wiki

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)
[![codecov](https://codecov.io/github/sata04/AAT/graph/badge.svg?token=I4FGAIJ6EQ)](https://codecov.io/github/sata04/AAT)
![Version](https://img.shields.io/badge/Version-10.0.0-brightgreen.svg)

> 微小重力環境の実験データを簡単に分析・可視化するためのデスクトップアプリケーション

---

## 📚 ドキュメント目次

### 🌟 はじめに

- **[[概要-Overview]]** - AATの概要、主な特徴、ユースケース
- **[[インストール-Installation]]** - システム要件とインストール手順
- **[[使い方-Usage]]** - 基本的な操作フローとデータ分析の始め方

### 🔬 解析機能

- **[[データ解析パイプライン-Data-Analysis-Pipeline]]** - データ処理の詳細フローとアルゴリズム
- **[[G-quality評価-G-quality-Evaluation]]** - 微小重力環境の品質評価機能
- **[[グラフと可視化-Graphs-and-Visualization]]** - グラフ表示とインタラクティブ機能

### 🖥️ ユーザーインターフェース

- **[[GUI操作ガイド-GUI-Guide]]** - メインウィンドウの構成と各種機能の使い方

### ⚙️ 開発者向け

- **[[プロジェクト構造-Project-Structure]]** - ディレクトリ構成とモジュール一覧
- **[[設定-Configuration]]** - 設定ファイルとパラメータの詳細
- **[[APIリファレンス-API-Reference]]** - コアモジュールのAPI仕様
- **[[開発者ガイド-Developer-Guide]]** - 開発環境のセットアップとコーディング規約
- **[[macOSアプリ配布-macOS-App-Distribution]]** - macOSアプリバンドルのビルドと配布

### 📖 リソース

- **[[使用例-Examples]]** - 具体的な使用例とサンプルコード
- **[[トラブルシューティング-Troubleshooting]]** - よくある問題と解決方法
- **[[変更履歴-Changelog]]** - バージョン履歴と変更内容
- **[[ライセンスと貢献-License-and-Contributing]]** - ライセンス情報と貢献ガイドライン

---

## 🚀 クイックスタート

### 1. インストール

```bash
git clone https://github.com/sata04/AAT.git
cd AAT
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. アプリケーションの起動

```bash
uv run python main.py
```

### 3. データ分析

1. 「CSVファイルを選択」ボタンをクリック
2. 分析したいCSVファイルを選択
3. データが自動的に処理され、グラフが表示されます！

詳細は **[[使い方-Usage]]** をご覧ください。

---

## 💡 主な特徴

- 📊 **簡単データ分析** - ファイル選択ボタンからCSVファイルを読み込むだけ
- 📈 **リアルタイム可視化** - 美しいグラフでデータを即座に表示
- 🔍 **詳細統計分析** - G-quality評価による高精度な微小重力環境評価
- 💾 **自動データ保存** - Excel形式での結果出力とグラフ画像の自動保存
- ⚡ **高速処理** - キャッシュ機能による高速な再処理
- 🖱️ **インタラクティブ** - グラフ上でのマウス操作による範囲選択分析
- 🎨 **モダンなUI** - ダーク/ライトモード切替とシステムテーマ連動

---

## 🎯 対象ユーザー

- **研究者** - 微小重力実験のデータを分析する科学者
- **エンジニア** - 宇宙実験装置の性能評価を行う技術者
- **学生** - 重力関連の研究に取り組む学生
- **開発者** - AATの開発に貢献したい方

---

## 📞 サポート・コンタクト

- 🐛 **バグ報告**: [GitHub Issues](https://github.com/sata04/AAT/issues)
- 💡 **機能リクエスト**: [GitHub Issues](https://github.com/sata04/AAT/issues)
- 📖 **ドキュメント**: このWikiをご覧ください

---

## 📄 ライセンス

このプロジェクトは [Apache License 2.0](https://github.com/sata04/AAT/blob/main/LICENSE.md) の下で公開されています。

---

<div align="center">

**AATを使用して素晴らしい微小重力実験データ分析を！** 🚀

Made with ❤️ for scientific research

---

*Code and documentation primarily created through AI collaboration (Vibe coding) with multiple AI tools including OpenAI Codex, Google Gemini, and Anthropic Claude*

</div>
