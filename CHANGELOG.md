# Changelog

All notable changes to AAT (Acceleration Analysis Tool) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 開発環境セットアップの改善
- Code quality toolsの統合（Ruff）
- CI/CDパイプライン（GitHub Actions）
- Pre-commitフックの設定
- VSCode設定ファイル
- 包括的なドキュメント（API、ユーザーマニュアル、開発者ガイド）

### Changed
- pyproject.tomlベースのプロジェクト構成に移行
- より厳密なコード品質基準の適用

### Fixed
- macOS環境でのPyQt6関連の警告を抑制

## [9.1.0] - 2024-12-01

### Added
- 出力ディレクトリ管理機能の強化
- エラーハンドリングの改善
- より詳細なログ出力

### Changed
- 同期点検出アルゴリズムの改善により精度が向上
- 時間軸調整ロジックの最適化
- UIレイアウトの細かな改善
- matplotlib互換性の向上（最新バージョン対応）

### Fixed
- 特定のCSVフォーマットで発生していた同期点検出エラー
- グラフ表示の軸ラベルが重なる問題
- キャッシュファイルの破損時のエラーハンドリング

## [9.0.0] - 2024-11-15

### Added
- バックグラウンド処理（QThread）によるUIの応答性向上
- グラフ上でのマウスドラッグによる範囲選択機能
- 選択範囲の詳細統計情報をリアルタイム表示
- 処理進捗をプログレスバーで表示
- キャッシュシステムの導入（pickle + HDF5）

### Changed
- アーキテクチャの大幅な改善（GUI/Core分離）
- データ処理パイプラインの最適化
- メモリ使用量の削減

### Fixed
- 大容量ファイル処理時のメモリリーク
- UIフリーズの問題
- エラー時のアプリケーションクラッシュ

### Security
- ファイルパスのサニタイゼーション強化


詳細な変更内容については、各リリースのGitHubリリースページを参照してください。

[Unreleased]: https://github.com/sata04/AAT/compare/v9.1.0...HEAD
[9.1.0]: https://github.com/sata04/AAT/compare/v9.0.0...v9.1.0
[9.0.0]: https://github.com/sata04/AAT/releases/tag/v9.0.0
