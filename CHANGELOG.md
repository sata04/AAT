# Changelog

All notable changes to AAT (Acceleration Analysis Tool) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [9.3.0] - 2025-08-09

### Changed
- デフォルト設定でのInner Capsule加速度反転オプション (`invert_inner_acceleration`) を `true` に変更
  - より直感的な加速度データ表示を実現
  - 既存の解析結果との一貫性を向上
- エクスポート機能の設定オプションを追加
  - 図表の幅・高さ設定 (`export_figure_width`, `export_figure_height`)
  - DPI設定 (`export_dpi`)

### Fixed
- デフォルト設定ファイルの一貫性を改善
- 設定値の検証とエラーハンドリングを強化

### Technical Changes
- アプリケーションバージョンを9.2.0から9.3.0に更新
- キャッシュシステムのバージョン管理により、設定変更に伴う自動再計算を実現

## [9.2.0] - 2025-08-08

### Added
- 開発環境セットアップの改善と自動化
- Code quality toolsの統合（Ruff linter/formatter）
- CI/CDパイプライン（GitHub Actions）の追加
- Pre-commitフックによる自動コード品質チェック
- VSCode設定ファイル（推奨拡張機能、設定）
- 包括的なドキュメント（API、ユーザーマニュアル、開発者ガイド）
- コマンドライン引数のサポート（--verbose, -v）
- 環境変数によるデバッグ制御（AAT_DEBUG, AAT_LOG_LEVEL）
- カスタム例外クラスによるエラーハンドリングの改善
- プロジェクト構造の最適化（config/, docs/ディレクトリ）

### Changed
- pyproject.tomlベースのプロジェクト構成に移行
- 依存関係管理をuvパッケージマネージャーに移行
- より厳密なコード品質基準の適用（Ruff設定）
- ロギングシステムの拡張と改善
- キャッシュ検証ロジックの改善
- データ処理パイプラインの最適化
- GUI応答性とエラーメッセージの改善

### Fixed
- macOS環境でのPyQt6関連の警告を抑制
- バックグラウンドワーカーのエラーハンドリング強化
- 設定ファイル検証の改善

### Security
- 入力検証の強化
- エラーメッセージの安全な表示

## [9.1.0] - 2025-05-25

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

## [9.0.0] - 2025-05-05

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

[Unreleased]: https://github.com/sata04/AAT/compare/v9.3.0...HEAD
[9.3.0]: https://github.com/sata04/AAT/compare/v9.2.0...v9.3.0
[9.2.0]: https://github.com/sata04/AAT/compare/v9.1.0...v9.2.0
[9.1.0]: https://github.com/sata04/AAT/compare/v9.0.0...v9.1.0
[9.0.0]: https://github.com/sata04/AAT/releases/tag/v9.0.0
