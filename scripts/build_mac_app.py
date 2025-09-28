#!/usr/bin/env python3
"""macOS向けのAATアプリケーションバンドルを生成するビルドスクリプト"""

from __future__ import annotations

import argparse
import importlib
import os
import platform
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageSequence

try:
    RESAMPLE = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover
    RESAMPLE = Image.LANCZOS  # type: ignore[attr-defined]

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _detect_default_icon() -> Path:
    for candidate in [
        PROJECT_ROOT / "favicon.ico",
        PROJECT_ROOT / "AATicon.png",
        PROJECT_ROOT / "AATicon.ico",
    ]:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("デフォルトアイコンが見つかりませんでした。--icon オプションでアイコンを指定してください。")


DEFAULT_ICON = _detect_default_icon()
BUILD_DIR = PROJECT_ROOT / "build"
RESOURCES_DIR = BUILD_DIR / "resources"
DIST_DIR = BUILD_DIR / "dist"
WORK_DIR = BUILD_DIR / "pyinstaller"
SPEC_DIR = BUILD_DIR / "spec"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AAT macOSアプリをビルドします")
    parser.add_argument(
        "--icon",
        type=Path,
        default=DEFAULT_ICON,
        help="アプリケーションアイコンへのパス (.icns または .ico/.png)。省略時は favicon.ico を使用",
    )
    parser.add_argument(
        "--bundle-identifier",
        default="jp.co.aat.app",
        help="macOSバンドル識別子 (例: com.example.app)",
    )
    return parser.parse_args()


def ensure_dirs() -> None:
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    SPEC_DIR.mkdir(parents=True, exist_ok=True)


def _select_largest_frame(icon: Image.Image) -> Image.Image:
    if getattr(icon, "n_frames", 1) == 1:
        return icon
    frames = [frame.copy() for frame in ImageSequence.Iterator(icon)]
    largest = max(frames, key=lambda img: img.width * img.height)
    return largest


def generate_icns(icon_path: Path, output_path: Path) -> Path:
    if icon_path.suffix.lower() == ".icns":
        return icon_path

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


def build(icon_path: Path, bundle_identifier: str) -> None:
    if platform.system() != "Darwin":
        raise RuntimeError("このビルドスクリプトはmacOS専用です。")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        DIST_DIR.mkdir(parents=True, exist_ok=True)

    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
        WORK_DIR.mkdir(parents=True, exist_ok=True)

    pyinstaller_args = [
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name=AAT",
        f"--icon={icon_path}",
        f"--distpath={DIST_DIR}",
        f"--workpath={WORK_DIR}",
        f"--specpath={SPEC_DIR}",
        f"--osx-bundle-identifier={bundle_identifier}",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtWidgets",
        f"--add-data={PROJECT_ROOT / 'config' / 'config.default.json'}{os.pathsep}config",
        f"--add-data={PROJECT_ROOT / 'docs' / 'user-manual.md'}{os.pathsep}docs",
        str(PROJECT_ROOT / "main.py"),
    ]

    pyinstaller_module = importlib.import_module("PyInstaller.__main__")
    pyinstaller_module.run(pyinstaller_args)


if __name__ == "__main__":
    arguments = parse_args()
    icon_to_use = prepare_icon(arguments.icon)
    build(icon_to_use, arguments.bundle_identifier)
    print(f"ビルドが完了しました。出力: {DIST_DIR / 'AAT.app'}")
