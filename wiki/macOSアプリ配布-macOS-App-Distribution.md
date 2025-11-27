# macOSアプリ配布 - macOS App Distribution

このページでは、macOS用のアプリバンドル（`.app`）とDMGファイルの作成方法を説明します。

> [!NOTE]
> 詳細情報は [docs/deployment-guide.md](https://github.com/sata04/AAT/blob/main/docs/deployment-guide.md) をご覧ください。

---

## 📋 前提条件

- **macOS**: 13以降（推奨）
- **Xcode Command Line Tools**: `xcode-select --install`
- **uv**: パッケージマネージャー
- **Python**: 3.10以上

---

## 🚀 ビルド手順

### 1. 依存関係のインストール

```bash
# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate

# ビルド用依存関係のインストール
uv pip install -e ".[build]"
```

これにより、以下がインストールされます:
- PyInstaller (≥6.10)
- Pillow (≥10.3)

### 2. ビルドスクリプトの実行

```bash
python scripts/build_mac_app.py
```

### 3. 出力の確認

以下のファイルが生成されます:

```
build/
├── dist/
│   └── AAT.app              # macOSアプリバンドル
└── dmg/
    └── AAT.dmg              # DMGインストーラー
```

---

## 🎨 カスタマイズオプション

### アイコンの変更

```bash
python scripts/build_mac_app.py --icon path/to/icon.png
```

対応フォーマット: `.png`, `.ico`, `.icns`

### DMG背景の変更

```bash
python scripts/build_mac_app.py --dmg-background path/to/background.tiff
```

### DMG作成をスキップ

```bash
python scripts/build_mac_app.py --skip-dmg
```

### ボリューム名の変更

```bash
python scripts/build_mac_app.py --volume-name "MyApp"
```

### 出力先の変更

```bash
python scripts/build_mac_app.py --dmg-output build/dmg/MyApp.dmg
```

---

## 📦 生成物の詳細

### AAT.app

macOSアプリバンドル:

```
AAT.app/
├── Contents/
│   ├── MacOS/
│   │   └── AAT              # 実行ファイル
│   ├── Resources/
│   │   ├── icon.icns        # アプリアイコン
│   │   └── ...              # その他のリソース
│   └── Info.plist           # アプリメタデータ
```

### AAT.dmg

DMGインストーラー:

- `/Applications`へのシンボリックリンク
- カスタム背景画像
- アプリアイコンの自動配置

---

## 🔐 署名と公証

### 署名（Codesign）

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  build/dist/AAT.app
```

### 公証（Notarization）

```bash
# DMGを作成
hdiutil create -volname "AAT" -srcfolder build/dist/AAT.app -ov -format UDZO build/dmg/AAT.dmg

# 公証を送信
xcrun notarytool submit build/dmg/AAT.dmg \
  --apple-id your@email.com \
  --password app-specific-password \
  --team-id TEAM_ID \
  --wait

# ステープル
xcrun stapler staple build/dmg/AAT.dmg
```

> [!WARNING]
> 署名と公証には、Apple Developer Programへの登録が必要です。

---

## 🧪 動作確認

### アプリの起動

```bash
open build/dist/AAT.app
```

### ログの確認

ターミナルから実行すると標準出力にログが流れます（ファイル出力はありません）:

```bash
AAT_LOG_LEVEL=DEBUG ./build/dist/AAT.app/Contents/MacOS/AAT
```
初回起動時にはフォントキャッシュが `~/Library/Application Support/AAT/matplotlib/` に作成されます。

---

## 🔧 トラブルシューティング

### ビルドエラー

```bash
# キャッシュをクリア
rm -rf build/ dist/

# 再ビルド
python scripts/build_mac_app.py
```

### 起動しない

```bash
# デバッグログ付きでターミナルから起動
AAT_LOG_LEVEL=DEBUG ./build/dist/AAT.app/Contents/MacOS/AAT
```

### アイコンが表示されない

アイコンファイルが有効か確認:

```bash
file resources/packaging/icons/app_icon.png
```

---

## 📊 ビルドサイズ

| ファイル | サイズ（目安） |
|---------|--------------|
| **AAT.app** | 約176MB |
| **AAT.dmg** | 約700MB（圧縮前） |

---

## 🚀 次のステップ

- **[Deployment Guide](https://github.com/sata04/AAT/blob/main/docs/deployment-guide.md)** - 詳細なデプロイ手順
- **[[開発者ガイド-Developer-Guide]]** - 開発環境の設定
- **[[トラブルシューティング-Troubleshooting]]** - 問題解決

[[Home]] に戻る
