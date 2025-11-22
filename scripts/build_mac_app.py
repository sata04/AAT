#!/usr/bin/env python3
"""macOS向けのAATアプリケーションバンドルとDMGを生成するビルドスクリプト"""

from __future__ import annotations

import argparse
import importlib
import io
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from plistlib import dump as plist_dump
from plistlib import load as plist_load
from tempfile import TemporaryDirectory

import tomllib
from PIL import Image, ImageSequence

try:
    RESAMPLE = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover
    RESAMPLE = Image.LANCZOS  # type: ignore[attr-defined]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGING_DIR = PROJECT_ROOT / "resources" / "packaging"
ICON_DIR = PACKAGING_DIR / "icons"
DMG_ASSETS_DIR = PACKAGING_DIR / "dmg"


def _detect_default_icon() -> Path:
    candidates = [
        ICON_DIR / "app_icon.icns",
        ICON_DIR / "app_icon.png",
        ICON_DIR / "AATicon.png",
        PROJECT_ROOT / "AATicon.png",
        PROJECT_ROOT / "AATicon.ico",
        PROJECT_ROOT / "favicon.ico",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "デフォルトアイコンが見つかりませんでした。resources/packaging/icons 配下か --icon オプションで指定してください。",
    )


DEFAULT_ICON = _detect_default_icon()
BUILD_DIR = PROJECT_ROOT / "build"
RESOURCES_DIR = BUILD_DIR / "resources"
DIST_DIR = BUILD_DIR / "dist"
WORK_DIR = BUILD_DIR / "pyinstaller"
SPEC_DIR = BUILD_DIR / "spec"
DMG_DIR = BUILD_DIR / "dmg"
DEFAULT_DMG_BACKGROUND = DMG_ASSETS_DIR / "dmg_background.tiff"
APP_NAME = "AAT"
VERSION_FALLBACK = "0.0.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AAT macOSアプリをビルドし、DMGも生成します")
    parser.add_argument(
        "--icon",
        type=Path,
        default=DEFAULT_ICON,
        help="アプリケーションアイコンへのパス (.icns または .ico/.png)。省略時は resources/packaging/icons の既定アイコンを使用",
    )
    parser.add_argument(
        "--bundle-identifier",
        default="jp.co.aat.app",
        help="macOSバンドル識別子 (例: com.example.app)",
    )
    parser.add_argument(
        "--dmg-background",
        type=Path,
        default=DEFAULT_DMG_BACKGROUND,
        help="DMG背景画像へのパス (.tiff 推奨)",
    )
    parser.add_argument(
        "--volume-name",
        default="AAT",
        help="DMGボリューム名",
    )
    parser.add_argument(
        "--skip-dmg",
        action="store_true",
        help=".app のみ生成し DMG は作らない場合に指定",
    )
    parser.add_argument(
        "--dmg-output",
        type=Path,
        default=DMG_DIR / "AAT.dmg",
        help="出力する DMG ファイルのパス",
    )
    return parser.parse_args()


def _safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def ensure_dirs() -> None:
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    DMG_DIR.mkdir(parents=True, exist_ok=True)


def _select_largest_frame(icon: Image.Image) -> Image.Image:
    if getattr(icon, "n_frames", 1) == 1:
        return icon
    frames = [frame.copy() for frame in ImageSequence.Iterator(icon)]
    largest = max(frames, key=lambda img: img.width * img.height)
    return largest


def generate_icns(icon_path: Path, output_path: Path) -> Path:
    if icon_path.suffix.lower() == ".icns":
        return icon_path

    if not icon_path.exists():
        raise FileNotFoundError(f"アイコンファイルが見つかりません: {icon_path}")

    if platform.system() != "Darwin":
        raise RuntimeError(".ico から .icns への変換はmacOSでのみサポートされています。事前に.icnsを用意してください。")

    if not icon_path.exists():
        raise FileNotFoundError(f"アイコンファイルが見つかりません: {icon_path}")

    if not shutil.which("iconutil"):
        raise RuntimeError("iconutil が見つかりません。Xcode Command Line Tools をインストールしてください。")

    with TemporaryDirectory() as tmpdir:
        iconset_dir = Path(tmpdir) / "AAT.iconset"
        iconset_dir.mkdir(parents=True, exist_ok=True)

        source = Image.open(icon_path).convert("RGBA")
        source = _select_largest_frame(source)

        sizes = [16, 32, 64, 128, 256, 512]
        for size in sizes:
            png_path = iconset_dir / f"icon_{size}x{size}.png"
            resized = source.resize((size, size), RESAMPLE)
            resized.save(png_path, format="PNG")

            retina_size = size * 2
            if retina_size <= 1024:
                retina_path = iconset_dir / f"icon_{size}x{size}@2x.png"
                retina_resized = source.resize((retina_size, retina_size), RESAMPLE)
                retina_resized.save(retina_path, format="PNG")

        # 1024pxのベースアイコンが無ければ追加
        if not (iconset_dir / "icon_512x512@2x.png").exists():
            largest = source.resize((1024, 1024), RESAMPLE)
            largest.save(iconset_dir / "icon_512x512@2x.png", format="PNG")

        subprocess.run(
            [
                "iconutil",
                "-c",
                "icns",
                str(iconset_dir),
                "-o",
                str(output_path),
            ],
            check=True,
        )

    return output_path


def prepare_icon(icon_argument: Path) -> Path:
    ensure_dirs()
    if icon_argument.suffix.lower() == ".icns" and icon_argument.exists():
        return icon_argument

    target_icon = RESOURCES_DIR / "app_icon.icns"
    return generate_icns(icon_argument, target_icon)


def read_project_version() -> str:
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as file:
            data = tomllib.load(file)
        return str(data.get("project", {}).get("version", VERSION_FALLBACK))
    except Exception:
        return VERSION_FALLBACK


def build_app(icon_path: Path, bundle_identifier: str) -> Path:
    if platform.system() != "Darwin":
        raise RuntimeError("このビルドスクリプトはmacOS専用です。")

    _safe_rmtree(DIST_DIR)
    _safe_rmtree(WORK_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    pyinstaller_args = [
        "--noconfirm",
        "--clean",
        "--windowed",
        f"--name={APP_NAME}",
        f"--icon={icon_path}",
        f"--distpath={DIST_DIR}",
        f"--workpath={WORK_DIR}",
        f"--specpath={SPEC_DIR}",
        f"--osx-bundle-identifier={bundle_identifier}",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        f"--add-data={PROJECT_ROOT / 'config' / 'config.default.json'}{os.pathsep}config",
        f"--add-data={PROJECT_ROOT / 'docs' / 'user-manual.md'}{os.pathsep}docs",
        str(PROJECT_ROOT / "main.py"),
    ]

    pyinstaller_module = importlib.import_module("PyInstaller.__main__")
    pyinstaller_module.run(pyinstaller_args)
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        raise FileNotFoundError(f"PyInstaller の出力が見つかりません: {app_path}")
    return app_path


def update_info_plist(app_path: Path, version: str) -> None:
    info_plist = app_path / "Contents" / "Info.plist"
    if not info_plist.exists():
        print(f"警告: Info.plist が見つからないためバージョンを書き込めません: {info_plist}")
        return

    try:
        with info_plist.open("rb") as file:
            plist_data = plist_load(file)
    except Exception as error:  # pragma: no cover - filesystem errors
        print(f"警告: Info.plist の読み込みに失敗しました ({error})")
        return

    plist_data["CFBundleShortVersionString"] = version
    plist_data["CFBundleVersion"] = version
    plist_data.setdefault("CFBundleName", APP_NAME)
    plist_data.setdefault("CFBundleDisplayName", APP_NAME)

    try:
        with info_plist.open("wb") as file:
            plist_dump(plist_data, file)
    except Exception as error:  # pragma: no cover - filesystem errors
        print(f"警告: Info.plist の書き込みに失敗しました ({error})")


def _mount_dmg(dmg_path: Path) -> Path:
    attach_result = subprocess.run(
        ["hdiutil", "attach", "-plist", "-readwrite", "-noverify", "-noautoopen", str(dmg_path)],
        check=True,
        capture_output=True,
    )
    plist = plist_load(io.BytesIO(attach_result.stdout))
    entities = plist.get("system-entities", [])
    mount_point = next((Path(ent["mount-point"]) for ent in entities if "mount-point" in ent), None)
    if not mount_point:
        raise RuntimeError("DMG のマウントに失敗しました")
    return mount_point


def _detach_dmg(mount_point: Path) -> None:
    attempts = [
        ["hdiutil", "detach", str(mount_point)],
        ["hdiutil", "detach", "-force", str(mount_point)],
    ]
    for command in attempts:
        result = subprocess.run(command)
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"DMG のアンマウントに失敗しました: {mount_point}")


def _wait_for_finder_write(mount_point: Path, timeout: float = 5.0) -> None:
    ds_store = mount_point / ".DS_Store"
    end_at = time.time() + timeout
    while time.time() < end_at:
        if ds_store.exists() and ds_store.stat().st_size > 0:
            return
        time.sleep(0.2)
    print("警告: .DS_Store が見つからない、またはサイズが 0 のためレイアウトが保存されない可能性があります。")


def _set_finder_layout(volume_name: str, app_name: str, background_name: str) -> None:
    applescript = f'''
tell application "Finder"
    tell disk "{volume_name}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        -- Tuned via Finder inspection; adjust if layout changes
        set bounds of container window to {{440, 230, 1041, 665}}
        set viewOptions to icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 128
        set background picture of viewOptions to file ".background:{background_name}"
        set position of item "{app_name}" to {{155, 198}}
        set position of item "Applications" to {{442, 198}}
        update without registering applications
        delay 2
        close
    end tell
end tell
'''
    subprocess.run(["osascript", "-e", applescript], check=True)


def create_dmg(app_path: Path, background_path: Path, volume_name: str, icon_path: Path, output_path: Path) -> Path:
    if not shutil.which("hdiutil"):
        raise RuntimeError("hdiutil が見つかりません。macOS で実行してください。")
    if not shutil.which("osascript"):
        raise RuntimeError("osascript が見つかりません。Finder でのレイアウト設定に必要です。")
    if not background_path.exists():
        raise FileNotFoundError(f"DMG 背景が見つかりません: {background_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dmg = output_path.with_suffix(".temp.dmg")
    for candidate in [output_path, temp_dmg]:
        if candidate.exists():
            candidate.unlink()

    with TemporaryDirectory() as tmpdir:
        staging_dir = Path(tmpdir) / "dmg_root"
        shutil.copytree(app_path, staging_dir / app_path.name)
        (staging_dir / "Applications").symlink_to("/Applications")

        background_dest = staging_dir / ".background" / background_path.name
        background_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(background_path, background_dest)
        if shutil.which("SetFile"):
            # Hide .background to keep Finder clean; ignore failures
            subprocess.run(["SetFile", "-a", "V", str(background_dest.parent)], check=False)

        volume_icon = None
        if icon_path.suffix.lower() == ".icns":
            volume_icon = staging_dir / ".VolumeIcon.icns"
            shutil.copy(icon_path, volume_icon)

        subprocess.run(
            [
                "hdiutil",
                "create",
                "-ov",
                "-format",
                "UDRW",
                "-srcfolder",
                str(staging_dir),
                "-volname",
                volume_name,
                "-fs",
                "HFS+",
                str(temp_dmg),
            ],
            check=True,
        )

        mount_point = _mount_dmg(temp_dmg)
        try:
            subprocess.run(["open", str(mount_point)])
            time.sleep(1)
            _set_finder_layout(volume_name, app_path.name, background_path.name)
            _wait_for_finder_write(mount_point, timeout=10.0)
            subprocess.run(["sync"])
            mounted_volume_icon = Path(mount_point) / ".VolumeIcon.icns"
            if volume_icon and mounted_volume_icon.exists() and shutil.which("SetFile"):
                try:
                    subprocess.run(["SetFile", "-a", "C", str(mount_point)], check=True)
                except subprocess.CalledProcessError as error:
                    print(f"警告: ボリュームアイコンの設定に失敗しました ({error})")
        finally:
            _detach_dmg(mount_point)

        subprocess.run(
            [
                "hdiutil",
                "convert",
                str(temp_dmg),
                "-format",
                "UDZO",
                "-imagekey",
                "zlib-level=9",
                "-o",
                str(output_path),
            ],
            check=True,
        )

    if temp_dmg.exists():
        temp_dmg.unlink()
    return output_path


def _resolve_background(path_from_cli: Path) -> Path:
    if path_from_cli.exists():
        return path_from_cli

    if path_from_cli != DEFAULT_DMG_BACKGROUND:
        raise FileNotFoundError(f"DMG の背景が見つかりませんでした: {path_from_cli}")

    fallback = DMG_ASSETS_DIR / "dmg_background.png"
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"DMG の背景が見つかりませんでした: {path_from_cli}")


def main() -> None:
    args = parse_args()
    icon_to_use = prepare_icon(args.icon)
    app_path = build_app(icon_to_use, args.bundle_identifier)
    version = read_project_version()
    update_info_plist(app_path, version)
    print(f"PyInstaller でのビルドが完了しました: {app_path}")

    if args.skip_dmg:
        return

    background_path = _resolve_background(args.dmg_background)
    dmg_path = create_dmg(app_path, background_path, args.volume_name, icon_to_use, args.dmg_output)
    print(f"DMG の作成が完了しました: {dmg_path}")


if __name__ == "__main__":
    main()
