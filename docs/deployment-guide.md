# AAT デプロイメントガイド

## 目次

1. [概要](#概要)
2. [ビルド環境の準備](#ビルド環境の準備)
3. [アプリケーションのビルド](#アプリケーションのビルド)
4. [配布パッケージの作成](#配布パッケージの作成)
5. [プラットフォーム別ガイド](#プラットフォーム別ガイド)
6. [コード署名と公証](#コード署名と公証)
7. [配布チャネル](#配布チャネル)
8. [インストーラーの作成](#インストーラーの作成)
9. [アップデート機構](#アップデート機構)
10. [トラブルシューティング](#トラブルシューティング)

---

## 概要

このガイドでは、AATアプリケーションを各プラットフォーム向けにビルドし、エンドユーザーに配布する方法について説明します。
> 注意: 現在のリポジトリにはPyInstaller用の`.spec`ファイルや`requirements.txt`は含まれていません。以下の手順はパッケージングのたたき台として利用し、実際には`pyproject.toml`/`uv.lock`に基づき `uv pip install -e ".[dev]"` で依存関係を用意した上で `pyinstaller` をセットアップしてください。

### 配布形式

| プラットフォーム | 配布形式 | ファイルサイズ（概算） |
|--------------|---------|------------------|
| Windows | .exe (実行可能ファイル) | 80-100 MB |
| macOS | .app (アプリケーションバンドル) | 90-110 MB |
| Linux | AppImage / .deb / .rpm | 85-105 MB |

### 必要なツール

- **PyInstaller**: Pythonアプリケーションの実行可能ファイル作成
- **setuptools**: Pythonパッケージング
- **Platform-specific tools**: 各OS固有のパッケージングツール

---

## ビルド環境の準備

### 1. 基本環境のセットアップ

```bash
# 仮想環境の作成
python -m venv build_env
source build_env/bin/activate  # Windows: build_env\Scripts\activate

# 依存関係のインストール
pip install -e ".[dev]"
pip install pyinstaller setuptools wheel pillow
```

### 2. PyInstallerのインストール

```bash
# 最新版のPyInstallerをインストール
pip install pyinstaller>=6.10

# 開発版が必要な場合
pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
```

### 3. ビルド用設定ファイルの準備

```python
# build_config.py
import sys
from pathlib import Path

# ビルド設定
BUILD_CONFIG = {
    'name': 'AAT',
    'version': '10.0.0',
    'description': 'Acceleration Analysis Tool',
    'author': 'AAT Development Team',
    'icon': 'assets/icon.ico' if sys.platform == 'win32' else 'assets/icon.icns',
    'bundle_identifier': 'com.zerogravity.aat',
}

# 含めるデータファイル
DATA_FILES = [
    ('config/config.default.json', 'config'),
    ('assets/*', 'assets'),
]

# 除外するモジュール
EXCLUDES = [
    'test',
    'tests',
    'unittest',
    'pytest',
]
```

---

## アプリケーションのビルド

### PyInstaller仕様ファイルの作成

```python
# aat.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/config.default.json', 'config'),
        ('LICENSE.md', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'matplotlib.backends.backend_qt5agg',
        'pandas',
        'numpy',
        'openpyxl',
        'tables',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'test',
        'tests',
        'unittest',
        'pytest',
        'ipython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AAT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUIアプリケーションなのでコンソールなし
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if sys.platform == 'win32' else 'assets/icon.icns',
)

# macOS用のアプリバンドル
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='AAT.app',
        icon='assets/icon.icns',
        bundle_identifier='com.zerogravity.aat',
        info_plist={
            'CFBundleName': 'AAT',
            'CFBundleDisplayName': 'Acceleration Analysis Tool',
            'CFBundleGetInfoString': "AAT - Acceleration Analysis Tool",
            'CFBundleIdentifier': "com.zerogravity.aat",
            'CFBundleVersion': "10.0.0",
            'CFBundleShortVersionString': "10.0.0",
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15.0',
        },
    )
```

### ビルドの実行

```bash
# 単一ファイルとしてビルド
pyinstaller --clean --onefile aat.spec

# ディレクトリとしてビルド（推奨）
pyinstaller --clean --onedir aat.spec

# デバッグ情報付きビルド
pyinstaller --clean --debug all aat.spec
```

---

## 配布パッケージの作成

### ディレクトリ構造

```
dist/
├── AAT/                    # Windows/Linux
│   ├── AAT.exe            # メイン実行ファイル
│   ├── config/
│   │   └── config.default.json
│   ├── _internal/         # 依存ライブラリ
│   └── README.txt
└── AAT.app/               # macOS
    └── Contents/
        ├── MacOS/
        │   └── AAT
        ├── Resources/
        └── Info.plist
```

---

## プラットフォーム別ガイド

### Windows

#### 必要な追加ツール
- **Visual C++ Redistributable**: 実行時に必要
- **NSIS**: インストーラー作成用（オプション）

#### ビルド手順
```batch
:: ビルド環境の準備
python -m venv build_env
build_env\Scripts\activate

:: 依存関係のインストール
pip install -e ".[dev]"
pip install pyinstaller

:: ビルド実行
pyinstaller --clean aat.spec

:: 配布パッケージの作成
:: パッケージングは手動で実行
```

#### Windows固有の考慮事項
- UAC（ユーザーアカウント制御）への対応
- アンチウイルスソフトによる誤検知対策
- 64ビット版と32ビット版の提供

### macOS

#### 必要な追加ツール
- **Xcode Command Line Tools**: コード署名用
- **create-dmg**: DMGファイル作成用

```bash
# ツールのインストール
xcode-select --install
brew install create-dmg
```

#### ビルド手順
```bash
# ビルド環境の準備
python3 -m venv build_env
source build_env/bin/activate

# 依存関係のインストール
pip install -e ".[dev]"
pip install pyinstaller

# ビルド実行
pyinstaller --clean aat.spec

# 配布パッケージの作成
# パッケージングは手動で実行
```

#### macOS固有の考慮事項
- コード署名と公証（Notarization）が必須
- Gatekeeper対応
- Universal Binary（Intel + Apple Silicon）の作成

### Linux

#### 配布形式の選択
- **AppImage**: 最も汎用的（推奨）
- **.deb**: Debian/Ubuntu系
- **.rpm**: RedHat/Fedora系
- **Flatpak**: 最新のサンドボックス形式

#### AppImageの作成
```bash
# AppImageToolのダウンロード
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# ビルドとパッケージング
pyinstaller --clean aat.spec
# パッケージングは手動で実行
```

---

## コード署名と公証

### Windows コード署名

```batch
:: 証明書の準備（.pfxファイル）
:: signtoolを使用した署名
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com AAT.exe
```

### macOS コード署名と公証

```bash
# 開発者証明書の確認
security find-identity -v -p codesigning

# コード署名
codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" AAT.app

# 公証用のZIP作成
ditto -c -k --keepParent AAT.app AAT.zip

# 公証の実行
xcrun notarytool submit AAT.zip --keychain-profile "AC_PASSWORD" --wait

# ステープル（公証情報の添付）
xcrun stapler staple AAT.app
```

### Linux 署名（オプション）

```bash
# GPG署名の作成
gpg --armor --detach-sign AAT-10.0.0-x86_64.AppImage
```

---

## 配布チャネル

### 1. GitHub Releases

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
        pip install pyinstaller

    - name: Build application
      run: pyinstaller --clean aat.spec

    # パッケージングステップは削除されました

    - name: Upload Release Asset
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        upload_url: ${{ github.event.release.upload_url }}
        asset_path: ./AAT-*.zip
        asset_name: AAT-${{ matrix.os }}.zip
        asset_content_type: application/zip
```

### 2. 公式ウェブサイト

```html
<!-- download.html -->
<div class="download-section">
    <h2>AAT v10.0.0 ダウンロード</h2>

    <div class="platform-downloads">
        <div class="windows">
            <h3>Windows</h3>
            <a href="/downloads/AAT-10.0.0-Windows-x64.zip" class="download-button">
                ダウンロード (ZIP, 95MB)
            </a>
            <p>Windows 10/11 (64-bit)</p>
        </div>

        <div class="macos">
            <h3>macOS</h3>
            <a href="/downloads/AAT-10.0.0-macOS.dmg" class="download-button">
                ダウンロード (DMG, 105MB)
            </a>
            <p>macOS 10.15以降</p>
        </div>

        <div class="linux">
            <h3>Linux</h3>
            <a href="/downloads/AAT-10.0.0-x86_64.AppImage" class="download-button">
                ダウンロード (AppImage, 98MB)
            </a>
            <p>ほとんどのLinuxディストリビューション</p>
        </div>
    </div>
</div>
```

### 3. パッケージマネージャー（将来対応）

```bash
# Homebrew (macOS)
brew install aat

# Snap (Linux)
snap install aat

# Chocolatey (Windows)
choco install aat
```

---

## インストーラーの作成

### Windows インストーラー（NSIS）

```nsis
; installer.nsi
!include "MUI2.nsh"

Name "AAT - Acceleration Analysis Tool"
OutFile "AAT-Setup-10.0.0.exe"
InstallDir "$PROGRAMFILES64\AAT"
RequestExecutionLevel admin

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "English"

; Installer Section
Section "AAT" SecMain
    SetOutPath "$INSTDIR"

    ; Copy files
    File /r "dist\AAT\*.*"

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\AAT"
    CreateShortcut "$SMPROGRAMS\AAT\AAT.lnk" "$INSTDIR\AAT.exe"
    CreateShortcut "$DESKTOP\AAT.lnk" "$INSTDIR\AAT.exe"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry entries
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AAT" \
                     "DisplayName" "AAT - Acceleration Analysis Tool"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AAT" \
                     "UninstallString" "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    Delete "$INSTDIR\*.*"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\AAT\*.*"
    RMDir "$SMPROGRAMS\AAT"
    Delete "$DESKTOP\AAT.lnk"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AAT"
SectionEnd
```

### macOS インストーラー（PKG）

```bash
# packages形式でのインストーラー作成
productbuild --distribution distribution.xml \
             --package-path . \
             --resources Resources \
             AAT-10.0.0-Installer.pkg

# 署名
productsign --sign "Developer ID Installer: Your Name (TEAM_ID)" \
            AAT-10.0.0-Installer-unsigned.pkg \
            AAT-10.0.0-Installer.pkg
```

---

## アップデート機構

### 自動アップデートの実装

```python
# core/updater.py
import requests
import json
from packaging import version
from PySide6.QtCore import QThread, Signal

class UpdateChecker(QThread):
    update_available = Signal(str)  # 新バージョン番号

    GITHUB_API_URL = "https://api.github.com/repos/sata04/AAT/releases/latest"

    def run(self):
        try:
            response = requests.get(self.GITHUB_API_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data['tag_name'].lstrip('v')

                from core.version import APP_VERSION
                if version.parse(latest_version) > version.parse(APP_VERSION):
                    self.update_available.emit(latest_version)
        except Exception as e:
            logger.error(f"アップデートチェック失敗: {e}")
```

### アップデート通知UI

```python
# gui/update_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class UpdateDialog(QDialog):
    def __init__(self, new_version, parent=None):
        super().__init__(parent)
        self.setWindowTitle("アップデート通知")

        layout = QVBoxLayout()

        message = QLabel(f"新しいバージョン {new_version} が利用可能です。")
        layout.addWidget(message)

        download_button = QPushButton("ダウンロードページを開く")
        download_button.clicked.connect(self.open_download_page)
        layout.addWidget(download_button)

        self.setLayout(layout)
```

---

## トラブルシューティング

### ビルド時の問題

#### ImportError: No module named 'xxx'
```bash
# hiddenimportsに追加
pyinstaller --hidden-import=missing_module aat.spec
```

#### アイコンが表示されない
```bash
# リソースファイルの明示的な追加
--add-data "assets/icon.png:assets"
```

#### ファイルサイズが大きすぎる
```bash
# 不要なモジュールの除外
--exclude-module matplotlib.tests
--exclude-module numpy.tests
```

### 実行時の問題

#### Windows: "VCRUNTIME140.dll が見つかりません"
- Visual C++ Redistributableのインストールが必要
- インストーラーに同梱するか、ダウンロードリンクを提供

#### macOS: "開発元が未確認のため開けません"
- コード署名と公証が必要
- 一時的な回避策: システム環境設定 → セキュリティとプライバシー

#### Linux: "Permission denied"
```bash
# 実行権限の付与
chmod +x AAT.AppImage
```

### デバッグ方法

```bash
# コンソール出力を有効にしてビルド
pyinstaller --console --debug all aat.spec

# 実行時のデバッグ
AAT.exe --debug  # Windows
./AAT.app/Contents/MacOS/AAT --debug  # macOS
./AAT.AppImage --debug  # Linux
```

---

このデプロイメントガイドは、AATを様々なプラットフォームで配布するための包括的な手順を提供します。継続的な改善とフィードバックにより、より良い配布プロセスを構築していきます。

最終更新日: 2025年11月22日
