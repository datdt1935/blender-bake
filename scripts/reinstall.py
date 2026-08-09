"""Reinstall the freshly built add-on into your local Blender.

Locates ``blender.exe`` (via the ``BLENDER_EXE`` environment variable, or common install
locations), then runs ``scripts/install_blender.py`` inside Blender **twice**: first an
``uninstall`` pass (remove every old copy and save prefs), then a fresh ``install`` pass.
Splitting the two into separate Blender processes is deliberate — installing in the same
process that already auto-loaded an old copy fails to enable with a stale-module ImportError.

Run ``scripts/build_zip.py`` first so the ZIP is up to date, then:

    python scripts/reinstall.py

Close the Blender GUI before running (an open instance can overwrite the saved prefs on
exit), and reopen Blender afterwards to pick up the new build.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "dist" / "auto_lowpoly_baker.zip"
INSTALL_SCRIPT = ROOT / "scripts" / "install_blender.py"


def find_blender() -> str:
    """Return the path to blender.exe, or exit with guidance if it cannot be found."""
    override = os.environ.get("BLENDER_EXE")
    if override:
        if Path(override).exists():
            return override
        raise SystemExit(f"BLENDER_EXE is set but does not exist: {override}")

    search_roots = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    ]
    candidates: list[Path] = []
    for root in search_roots:
        foundation = Path(root, "Blender Foundation")
        if foundation.exists():
            candidates.extend(foundation.glob("Blender */blender.exe"))
    # Steam install fallback.
    for root in search_roots:
        candidates.extend(Path(root, "Steam", "steamapps", "common").glob("Blender/blender.exe"))

    existing = sorted({path for path in candidates if path.exists()})
    if not existing:
        raise SystemExit(
            "Could not find blender.exe automatically. Set the BLENDER_EXE environment "
            "variable to your Blender executable, e.g.\n"
            '  set BLENDER_EXE="C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe"'
        )

    # Highest version sorts last.
    return str(existing[-1])


def run_phase(blender: str, phase: str) -> int:
    """Run one install_blender.py phase in its own Blender process."""
    completed = subprocess.run(
        [blender, "--background", "--python", str(INSTALL_SCRIPT), "--", phase],
        cwd=str(ROOT),
        check=False,
    )
    return completed.returncode


def main() -> None:
    if not ZIP_PATH.exists():
        raise SystemExit(f"Build not found: {ZIP_PATH}\nRun 'python scripts/build_zip.py' first.")

    blender = find_blender()
    print(f"Using Blender: {blender}")
    print(f"Installing:    {ZIP_PATH}")

    print("[1/2] Removing any previously installed copy...")
    # A non-zero uninstall code is non-fatal: there may be nothing to remove.
    run_phase(blender, "uninstall")

    print("[2/2] Installing the new build in a fresh Blender process...")
    if run_phase(blender, "install") != 0:
        raise SystemExit("Reinstall failed during the install pass.")

    print("Reinstall complete. Reopen Blender to use the new build.")


if __name__ == "__main__":
    main()
