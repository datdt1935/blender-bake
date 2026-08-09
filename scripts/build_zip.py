"""Build an installable ZIP for Auto Lowpoly Baker."""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "auto_lowpoly_baker"
BUILD_INFO = PACKAGE / "build_info.py"
DIST = ROOT / "dist"
ZIP_PATH = DIST / "auto_lowpoly_baker.zip"

EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_DIRS = {"__pycache__"}

BUILD_NUMBER_PATTERN = re.compile(r"^BUILD_NUMBER\s*=\s*(\d+)", re.MULTILINE)


def bump_build_number() -> int:
    """Increment BUILD_NUMBER in build_info.py and return the new value."""
    text = BUILD_INFO.read_text(encoding="utf-8")
    match = BUILD_NUMBER_PATTERN.search(text)
    if match is None:
        raise SystemExit(f"Could not find BUILD_NUMBER in {BUILD_INFO}")

    new_number = int(match.group(1)) + 1
    updated = BUILD_NUMBER_PATTERN.sub(f"BUILD_NUMBER = {new_number}", text, count=1)
    BUILD_INFO.write_text(updated, encoding="utf-8")
    return new_number


def should_include(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_DIRS:
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return True


def main() -> None:
    if not PACKAGE.exists():
        raise SystemExit(f"Package folder not found: {PACKAGE}")

    build_number = bump_build_number()

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE.rglob("*")):
            if path.is_file() and should_include(path):
                archive.write(path, path.relative_to(ROOT))

    print(f"Built {ZIP_PATH} (build {build_number})")


if __name__ == "__main__":
    main()
