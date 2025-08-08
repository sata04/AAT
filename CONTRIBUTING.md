# AAT への貢献ガイド

AAT (Acceleration Analysis Tool) プロジェクトへの貢献を検討いただき、ありがとうございます！このガイドでは、プロジェクトに貢献する方法について説明します。

## 目次

1. [行動規範](#行動規範)
2. [貢献の方法](#貢献の方法)
3. [開発環境のセットアップ](#開発環境のセットアップ)
4. [開発プロセス](#開発プロセス)
5. [コーディング規約](#コーディング規約)
6. [コミットメッセージ](#コミットメッセージ)
7. [プルリクエスト](#プルリクエスト)
8. [Issue の報告](#issue-の報告)
9. [ドキュメントへの貢献](#ドキュメントへの貢献)
10. [コミュニティ](#コミュニティ)

---

## 行動規範

### 私たちの約束

オープンで友好的な環境を育むために、貢献者および維持管理者として、年齢、体型、障害、民族性、性別、性的指向、国籍、外見、人種、宗教、性的アイデンティティに関わらず、すべての人々にとってハラスメントのない体験を提供することを約束します。

### 期待される行動

- 友好的で包括的な言葉を使用する
- 異なる視点や経験を尊重する
- 建設的な批判を優雅に受け入れる
- コミュニティにとって最善のことに焦点を当てる
- 他のコミュニティメンバーに対して共感を示す

### 受け入れられない行動

- 性的な言葉や画像の使用、歓迎されない性的関心や誘い
- トローリング、侮辱的/軽蔑的なコメント、個人的または政治的攻撃
- 公的または私的なハラスメント
- 明示的な許可なく、他者の個人情報を公開すること
- その他、プロフェッショナルな環境で不適切と合理的に考えられる行為

---

## 貢献の方法

### 1. バグ報告

バグを発見した場合は、[GitHub Issues](https://github.com/sata04/AAT/issues) で報告してください。

**バグ報告に含めるべき情報:**
- バグの明確で詳細な説明
- バグを再現する手順
- 期待される動作
- 実際の動作
- スクリーンショット（該当する場合）
- 環境情報（OS、Pythonバージョン、AATバージョン）

### 2. 機能リクエスト

新機能のアイデアがある場合は、Issue を作成して提案してください。

**機能リクエストに含めるべき情報:**
- 機能の詳細な説明
- なぜその機能が必要か
- 可能な実装方法
- 代替案（ある場合）

### 3. コードの貢献

コードの貢献は以下の手順で行います：

1. リポジトリをフォーク
2. 機能ブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'feat: Add amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを作成

### 4. ドキュメントの改善

ドキュメントの誤り、不明確な説明、追加すべき情報がある場合は、遠慮なく修正してください。

---

## 開発環境のセットアップ

### 必要なツール

- Python 3.9 以上
- Git
- 推奨: VSCode または PyCharm

### セットアップ手順

```bash
# 1. リポジトリをフォーク（GitHubで）

# 2. フォークをクローン
git clone https://github.com/YOUR_USERNAME/AAT.git
cd AAT

# 3. アップストリームを追加
git remote add upstream https://github.com/sata04/AAT.git

# 4. 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 5. 開発依存関係をインストール
pip install -e ".[dev]"

# 6. pre-commitフックをセットアップ
pre-commit install

# 7. 動作確認
python main.py --debug
```

---

## 開発プロセス

### 1. 最新の変更を取得

```bash
git checkout main
git pull upstream main
git push origin main
```

### 2. 新しい機能ブランチを作成

```bash
git checkout -b feature/your-feature-name
```

### 3. 開発とテスト

```bash
# コードを編集

# テストを実行
pytest

# リントチェック
ruff check .
ruff format .

# 型チェック（将来実装予定）
# mypy .
```

### 4. コミット

```bash
# 変更をステージング
git add .

# コミット（Conventional Commitsに従う）
git commit -m "feat: Add new analysis feature"
```

### 5. プッシュとPR作成

```bash
# ブランチをプッシュ
git push origin feature/your-feature-name

# GitHubでプルリクエストを作成
```

---

## コーディング規約

### Python スタイルガイド

プロジェクトは [Ruff](https://github.com/astral-sh/ruff) を使用してコードスタイルを管理しています。

**主なルール:**
- インデント: スペース4つ
- 行の最大長: 120文字
- 文字列: ダブルクォート使用
- docstring: Google スタイル

### コード例

```python
from typing import Optional, List, Dict, Any
import pandas as pd

class DataAnalyzer:
    """データ分析クラス
    
    微小重力実験データの分析機能を提供します。
    
    Attributes:
        config: 設定辞書
        logger: ロガーインスタンス
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self.logger = get_logger(__name__)
        
    def analyze(
        self,
        data: pd.DataFrame,
        window_size: Optional[float] = None
    ) -> Dict[str, float]:
        """データを分析
        
        Args:
            data: 分析対象のデータフレーム
            window_size: ウィンドウサイズ（秒）、Noneの場合は設定値を使用
            
        Returns:
            分析結果の辞書
            
        Raises:
            ValueError: データが不正な場合
        """
        if data.empty:
            raise ValueError("データが空です")
            
        window_size = window_size or self.config.get("window_size", 0.1)
        
        # 分析処理
        results = self._perform_analysis(data, window_size)
        
        self.logger.info(f"分析完了: {len(data)}件のデータを処理")
        return results
```

### 型ヒント

すべての関数に型ヒントを追加してください：

```python
def calculate_mean(values: List[float]) -> float:
    """平均値を計算"""
    return sum(values) / len(values)

def process_data(
    file_path: str,
    config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """データを処理"""
    config = config or {}
    # 処理...
```

### エラーハンドリング

```python
from core.exceptions import DataLoadError
from core.logger import get_logger

logger = get_logger(__name__)

def safe_operation():
    try:
        # 危険な操作
        result = risky_operation()
    except SpecificError as e:
        logger.error(f"特定のエラーが発生: {e}")
        # 適切なエラーハンドリング
        raise DataLoadError("データ読み込みに失敗しました") from e
    except Exception as e:
        logger.exception("予期しないエラー")
        raise
    else:
        logger.info("操作が成功しました")
        return result
    finally:
        # クリーンアップ処理
        cleanup()
```

---

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 仕様に従ってください。

### フォーマット

```
<type>(<scope>): <subject>

<body>

<footer>
```

### タイプ

- **feat**: 新機能
- **fix**: バグ修正
- **docs**: ドキュメントのみの変更
- **style**: コードの意味に影響しない変更（空白、フォーマット等）
- **refactor**: バグ修正や機能追加を含まないコード変更
- **perf**: パフォーマンス改善
- **test**: テストの追加や修正
- **build**: ビルドシステムや外部依存関係の変更
- **ci**: CI設定ファイルやスクリプトの変更
- **chore**: その他の変更（ビルドプロセスやツールの変更）

### 例

```bash
# 新機能
git commit -m "feat(statistics): Add RMS calculation function"

# バグ修正
git commit -m "fix(gui): Resolve graph update issue on Windows"

# ドキュメント
git commit -m "docs: Update installation instructions for Linux"

# リファクタリング
git commit -m "refactor(cache): Simplify cache key generation logic"

# Breaking change
git commit -m "feat(api)!: Change return type of calculate_statistics

BREAKING CHANGE: calculate_statistics now returns a dict instead of tuple"
```

---

## プルリクエスト

### PR作成前のチェックリスト

- [ ] コードがプロジェクトのスタイルガイドに従っている
- [ ] 自己レビューを実施した
- [ ] コメントを追加した（特に複雑な部分）
- [ ] ドキュメントを更新した（必要な場合）
- [ ] 変更によって既存機能が壊れていない
- [ ] テストを追加した（新機能の場合）
- [ ] すべてのテストが通る
- [ ] リントエラーがない

### PRテンプレート

```markdown
## 概要
変更の簡潔な説明

## 変更内容
- [ ] 機能Aを実装
- [ ] バグBを修正
- [ ] テストを追加

## 変更の種類
- [ ] バグ修正 (非破壊的変更)
- [ ] 新機能 (非破壊的変更)
- [ ] 破壊的変更 (既存機能に影響)

## テスト方法
1. アプリケーションを起動
2. 〇〇を実行
3. △△が表示されることを確認

## スクリーンショット（該当する場合）
変更前：
変更後：

## 関連Issue
Closes #123
```

### レビュープロセス

1. **自動チェック**: CI/CDパイプラインが自動的に実行されます
2. **コードレビュー**: 他の開発者がコードをレビューします
3. **フィードバック**: レビューコメントに対応してください
4. **承認**: 承認後、メンテナーがマージします

---

## Issue の報告

### Issue テンプレート

#### バグ報告
```markdown
**バグの説明**
バグの明確で簡潔な説明

**再現手順**
1. '...'に移動
2. '...'をクリック
3. '...'までスクロール
4. エラーを確認

**期待される動作**
期待される動作の明確で簡潔な説明

**スクリーンショット**
該当する場合は、問題を説明するスクリーンショットを追加

**環境:**
 - OS: [例: Windows 10]
 - Python: [例: 3.9.5]
 - AAT Version: [例: 9.1.0]

**追加情報**
問題に関するその他の情報
```

#### 機能リクエスト
```markdown
**機能の説明**
提案する機能の明確で簡潔な説明

**動機**
なぜこの機能が必要か、どのような問題を解決するか

**提案する解決策**
どのように実装すべきか

**代替案**
検討した他の解決策

**追加情報**
機能リクエストに関するその他の情報
```

---

## ドキュメントへの貢献

### ドキュメントの種類

1. **APIドキュメント** (`docs/api-reference.md`)
   - 関数、クラス、メソッドの説明
   - パラメータと戻り値
   - 使用例

2. **ユーザーガイド** (`docs/user-manual.md`)
   - 操作手順
   - トラブルシューティング
   - FAQ

3. **開発者ガイド** (`docs/developer-guide.md`)
   - アーキテクチャ説明
   - 開発環境構築
   - コーディング規約

### ドキュメント作成のガイドライン

- 明確で簡潔な日本語を使用
- 技術用語は適切に説明
- コード例を含める
- スクリーンショットを活用（GUIの説明時）
- 更新日を記載

---

## コミュニティ

### 質問とサポート

- **GitHub Discussions**: 一般的な質問や議論
- **GitHub Issues**: バグ報告と機能リクエスト
- **Email**: [プロジェクトメンテナーに連絡]

### 貢献者の認識

すべての貢献者は、その貢献の大小に関わらず、プロジェクトにとって価値があります。貢献者は以下に記載されます：

- `README.md` の Contributors セクション
- GitHub の Contributors ページ
- リリースノート（該当する場合）

### ライセンス

このプロジェクトに貢献することにより、あなたの貢献が [Apache License 2.0](LICENSE.md) の下でライセンスされることに同意したものとみなされます。

---

## さいごに

AATプロジェクトへの貢献を検討いただき、ありがとうございます。あなたの貢献により、このツールがより多くの研究者にとって有用なものになることを楽しみにしています。

質問がある場合は、遠慮なく Issue を作成するか、メンテナーに連絡してください。

Happy Coding! 🚀