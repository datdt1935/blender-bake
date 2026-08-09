"""Reinstall Auto Lowpoly Baker into the Blender that runs this script.

This is meant to be executed *inside* Blender, in background mode:

    blender --background --python scripts/install_blender.py -- <phase>

`<phase>` is one of:

- ``uninstall`` — disable and remove every installed copy (extension and legacy), save prefs.
- ``install``   — install ``dist/auto_lowpoly_baker.zip``, enable it, save prefs.
- ``all``       — do both in one process (default; not recommended when an old copy is loaded).

Prefer running it through ``scripts/reinstall.py``, which launches two Blender processes —
``uninstall`` then ``install`` — so the install never sees a stale, already-loaded copy of
the module (which otherwise breaks enabling with an ImportError).

It tries the Blender 4.2+ extensions API first and falls back to the legacy add-on API, so it
works whether the package is registered as an extension or a legacy add-on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

ADDON_ID = "auto_lowpoly_baker"
ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "dist" / f"{ADDON_ID}.zip"

# Module names Blender may use for this package (legacy add-on vs. extension repo).
MODULE_CANDIDATES = (ADDON_ID, f"bl_ext.user_default.{ADDON_ID}")


def log(message: str) -> None:
    print(f"[reinstall] {message}")


def try_call(description: str, func) -> bool:
    """Run a best-effort step, logging success or the reason it was skipped."""
    try:
        func()
    except Exception as exc:  # noqa: BLE001 - Blender API varies across versions
        log(f"skip: {description} ({type(exc).__name__}: {exc})")
        return False
    log(f"ok: {description}")
    return True


def parse_phase() -> str:
    """Read the phase argument passed after ``--`` on the Blender command line."""
    argv = sys.argv
    if "--" in argv:
        extra = argv[argv.index("--") + 1:]
        if extra:
            return extra[0]
    return "all"


def disable_existing() -> None:
    """Disable any currently enabled copy of the add-on."""
    import addon_utils

    for module in addon_utils.modules():
        name = module.__name__
        if name == ADDON_ID or name.endswith(f".{ADDON_ID}"):
            try_call(f"disable {name}", lambda n=name: addon_utils.disable(n, default_set=True))


def remove_existing() -> None:
    """Remove any previously installed copy (legacy add-on or extension package).

    Avoids ``bpy.ops.preferences.addon_remove``: in ``--background`` mode that operator
    crashes on ``context.area.tag_redraw()`` and can leave a dangling enabled entry in
    the preferences that errors on the next startup. Instead we clear the prefs entry
    directly and delete the legacy folder ourselves.
    """
    import shutil

    prefs = bpy.context.preferences

    # Drop any enabled entry so the next startup does not try to load a removed module.
    for name in MODULE_CANDIDATES:
        entry = prefs.addons.get(name)
        if entry is not None:
            try_call(f"drop prefs entry {name}", lambda e=entry: prefs.addons.remove(e))

    # Delete the legacy add-on folder from the user scripts/addons directory.
    legacy = Path(bpy.utils.user_resource("SCRIPTS", path="addons")) / ADDON_ID
    if legacy.exists():
        try_call(f"delete legacy folder {legacy}", lambda: shutil.rmtree(legacy))

    # Uninstall the extension package from every repo that has it.
    extensions = getattr(prefs, "extensions", None)
    repos = getattr(extensions, "repos", []) if extensions else []
    for index, repo in enumerate(repos):
        repo_name = getattr(repo, "module", index)
        try_call(
            f"uninstall extension from repo '{repo_name}'",
            lambda i=index: bpy.ops.extensions.package_uninstall(repo_index=i, pkg_id=ADDON_ID),
        )


def enable_installed() -> bool:
    """Enable whichever module name Blender registered for the package."""
    for name in MODULE_CANDIDATES:
        if try_call(f"enable {name}", lambda n=name: bpy.ops.preferences.addon_enable(module=n)):
            return True
    return False


def install() -> bool:
    """Install the built ZIP, preferring the extensions API, then the legacy API."""
    zip_path = str(ZIP_PATH)

    extensions_ops = getattr(bpy.ops, "extensions", None)
    if extensions_ops and hasattr(extensions_ops, "package_install_files"):
        for kwargs in (
            {"filepath": zip_path, "repo": "user_default", "enable_on_install": True},
            {"filepath": zip_path, "enable_on_install": True},
            {"filepath": zip_path},
        ):
            if try_call(
                f"extensions.package_install_files({sorted(kwargs)})",
                lambda k=kwargs: bpy.ops.extensions.package_install_files(**k),
            ):
                enable_installed()
                return True

    if try_call(
        "preferences.addon_install",
        lambda: bpy.ops.preferences.addon_install(overwrite=True, filepath=zip_path),
    ):
        enable_installed()
        return True

    return False


def main() -> None:
    phase = parse_phase()
    log(f"phase: {phase}")

    if phase in ("uninstall", "all"):
        disable_existing()
        remove_existing()

    installed = True
    if phase in ("install", "all"):
        if not ZIP_PATH.exists():
            log(f"ERROR: build not found: {ZIP_PATH} (run scripts/build_zip.py first)")
            sys.exit(1)
        log(f"installing from {ZIP_PATH}")
        installed = install()

    try_call("save user preferences", lambda: bpy.ops.wm.save_userpref())

    if not installed:
        log("ERROR: could not install the add-on with any known Blender method.")
        sys.exit(1)

    log(f"phase '{phase}' done.")


if __name__ == "__main__":
    main()
