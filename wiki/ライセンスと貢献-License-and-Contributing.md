# ライセンスと貢献 - License and Contributing

このページでは、AATのライセンス情報とプロジェクトへの貢献方法について説明します。

---

## 📄 ライセンス

AATは **Apache License 2.0** の下で公開されています。

### Apache License 2.0 の概要

- ✅ **商用利用可能**: 商用プロジェクトでの使用が許可されています
- ✅ **修正可能**: コードを自由に修正できます
- ✅ **配布可能**: 修正版を配布できます
- ✅ **特許利用許可**: コントリビューターから特許使用許諾が付与されます
- ⚠️ **ライセンス表記必須**: ライセンスと著作権表示を含める必要があります
- ⚠️ **免責事項**: ソフトウェアは「現状のまま」提供され、保証はありません

### 完全なライセンス文

完全なライセンス文は [LICENSE.md](../LICENSE.md) をご覧ください。

---

## 🤝 貢献ガイド

AATへの貢献を歓迎します！以下の方法で貢献できます。

### 貢献の種類

1. **バグ報告** - 問題を発見したら報告してください
2. **機能リクエスト** - 新機能のアイデアを提案してください
3. **コード貢献** - バグ修正や新機能の実装
4. **ドキュメント改善** - ドキュメントの追加・修正
5. **テスト追加** - テストカバレッジの向上
6. **翻訳** - 多言語対応の支援

---

## 🐛 バグ報告

バグを発見した場合:

1. **既存のIssueを確認**
   - [GitHub Issues](https://github.com/sata04/AAT/issues)で同様の報告がないか確認

2. **新しいIssueを作成**
   - 以下の情報を含めてください:
     - **OS**: macOS 14.2、Windows 11など
     - **AATバージョン**: 10.0.0など
     - **Pythonバージョン**: 3.10.5など
     - **エラーメッセージ**: 表示されたエラーの全文
     - **再現手順**: バグを再現する詳細な手順
     - **期待される動作**: 本来どう動作すべきか
     - **スクリーンショット**: 可能であれば添付

3. **ログファイルの添付**
   - ターミナルから `AAT_LOG_LEVEL=DEBUG uv run python main.py` を実行し、コンソール出力を添付

---

## 💡 機能リクエスト

新機能を提案する場合:

1. **[GitHub Issues](https://github.com/sata04/AAT/issues)で新しいIssueを作成**

2. **以下を明確に記載**:
   - **機能の説明**: 何を実現したいか
   - **ユースケース**: どのような場面で役立つか
   - **期待される動作**: 具体的にどう動作すべきか
   - **既存機能との関係**: 既存機能への影響

3. **タイトルに`[Feature Request]`を付ける**

---

## 💻 コード貢献

### 貢献の流れ

1. **リポジトリをフォーク**
   ```bash
   # GitHubでフォークボタンをクリック
   git clone https://github.com/YOUR_USERNAME/AAT.git
   cd AAT
   ```

2. **ブランチを作成**
   ```bash
   git checkout -b feature/my-awesome-feature
   # または
   git checkout -b fix/bug-description
   ```

3. **開発環境をセットアップ**
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   uv run pre-commit install
   ```

4. **変更を実装**
   - コーディング規約に従う
   - テストを追加
   - ドキュメントを更新

5. **テストを実行**
   ```bash
   uv run pytest
   uv run ruff check . --fix
   uv run ruff format .
   ```

6. **変更をコミット**
   ```bash
   git add .
   git commit -m "feat: Add awesome new feature"
   ```

   コミットメッセージのフォーマット:
   - `feat:` 新機能
   - `fix:` バグ修正
   - `docs:` ドキュメント変更
   - `test:` テスト追加・修正
   - `refactor:` リファクタリング
   - `style:` コードスタイル変更

7. **プッシュ**
   ```bash
   git push origin feature/my-awesome-feature
   ```

8. **Pull Requestを作成**
   - GitHubでPull Requestを作成
   - 変更内容を明確に記載
   - 関連するIssueをリンク

### Pull Requestのガイドライン

- **1つのPRは1つの目的**: 複数の機能を1つのPRに含めない
- **小さく保つ**: レビューしやすいサイズに分割
- **テストを含める**: 新機能には必ずテストを追加
- **ドキュメントを更新**: 必要に応じてREADMEやWikiを更新
- **レビューに対応**: レビュアーのフィードバックに誠実に対応

---

## 📝 ドキュメント貢献

ドキュメントの改善は非常に価値があります:

1. **誤字・脱字の修正**
2. **説明の追加・改善**
3. **新しい使用例の追加**
4. **Wikiページの追加・改善**
5. **翻訳（英語版など）**

ドキュメントの貢献も通常のコード貢献と同じフローです。

---

## 🧪 テスト貢献

テストカバレッジの向上に協力してください:

1. **未カバーのコードを特定**
   ```bash
   uv run pytest  # addoptsで--cov/--cov-report=html:htmlcovが有効
   open htmlcov/index.html
   ```

2. **テストを追加**
   - ユニットテスト: `tests/test_*.py`
   - GUIテスト: `pytest-qt`を使用

3. **エッジケースのテスト**
   - 境界値テスト
   - エラーハンドリングのテスト

---

## 📋 コーディング規約

詳細は **[[開発者ガイド-Developer-Guide]]** を参照してください。

### 主要なルール

- **PEP 8**に準拠
- 行の長さ: 最大120文字
- docstringを記載
- 型ヒントを使用
- Ruffによる自動フォーマット

---

## 🎖️ コントリビューター

AATに貢献してくださったすべての方に感謝します！

貢献者リストは [GitHub Contributors](https://github.com/sata04/AAT/graphs/contributors) でご覧いただけます。

### 🤖 AI協力者

AATのコードとドキュメントは、**Vibe coding**（AIとの協働プログラミング）手法により作成されています。

OpenAI Codex、Google Gemini、Anthropic Claudeをはじめとする複数のAIツールを駆使し、AIが主体的にコードとドキュメントを生成し、人間の開発者がそれをレビュー、テスト、調整、承認するという協働開発を行っています。

---

## 📞 連絡先

質問や提案がある場合:

- **GitHub Issues**: [https://github.com/sata04/AAT/issues](https://github.com/sata04/AAT/issues)
- **Pull Requests**: [https://github.com/sata04/AAT/pulls](https://github.com/sata04/AAT/pulls)

---

## 🔗 関連リンク

- [完全な貢献ガイド](../CONTRIBUTING.md)
- [開発者ガイド](../docs/developer-guide.md)
- [テストガイド](../docs/testing-guide.md)

---

<div align="center">

**AATへの貢献をお待ちしています！** 🚀

Made with ❤️ for scientific research

</div>
