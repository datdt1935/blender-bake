"""Build an installable ZIP for Auto Lowpoly Baker."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "auto_lowpoly_baker"
DIST = ROOT / "dist"
ZIP_PATH = DIST / "auto_lowpoly_baker.zip"

EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_DIRS = {"__pycache__"}


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

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE.rglob("*")):
            if path.is_file() and should_include(path):
                archive.write(path, path.relative_to(ROOT))

    print(f"Built {ZIP_PATH}")


if __name__ == "__main__":
    main()
