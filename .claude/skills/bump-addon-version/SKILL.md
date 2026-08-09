---
name: bump-addon-version
description: Bump and synchronize the Auto Lowpoly Baker add-on version whenever the add-on's behavior changes or before building/releasing, then rebuild and reinstall it into the local Blender. Use when the user says things like "bump version", "release the addon", "build the addon", "new version", "reinstall the addon", or after adding/changing an operator, panel, property, or fix. Keeps the version in __init__.py (bl_info) and blender_manifest.toml in sync, adds a CHANGELOG entry, rebuilds the ZIP, and uninstalls the old copy then installs the new build in Blender.
---

# Bump Auto Lowpoly Baker version

Keep the add-on's semantic version correct and consistent across every file whenever the
add-on changes or is built. This is the semantic version (e.g. `1.6.0`) that identifies a
release — it is **separate** from the auto-incrementing build counter in `build_info.py`,
which `scripts/build_zip.py` bumps on its own and must not be edited by hand.

## When to run this

Run these steps when:

- The user asks to build, release, package, publish, or "make a new version" of the add-on.
- You just added or changed user-facing behavior: an operator, a panel section, a property,
  a bug fix, or a workflow change — and the change is ready to ship.

If you only made an internal/no-op change (comments, refactor with identical behavior), do
**not** bump; just note that no version change is needed.

## Version policy (semver: MAJOR.MINOR.PATCH)

Decide the bump from the nature of the change since the last version:

- **PATCH** (`1.6.0 -> 1.6.1`): bug fix, wording, or a small tweak with no new capability.
- **MINOR** (`1.6.0 -> 1.7.0`): a new feature or option that is backward compatible — a new
  button, operator, panel section, or setting.
- **MAJOR** (`1.6.0 -> 2.0.0`): a breaking change — removed/renamed operators or properties,
  or a workflow that behaves incompatibly. Confirm with the user before a MAJOR bump.

If several changes are batched, pick the highest-severity bump that applies (one feature +
one fix = MINOR).

## Files to update (keep all in sync)

The version lives in two places and they must always match:

1. `auto_lowpoly_baker/__init__.py` — the `bl_info` dict:
   ```python
   "version": (1, 6, 0),
   ```
   Update the tuple, e.g. `(1, 7, 0)`.

2. `auto_lowpoly_baker/blender_manifest.toml` — the string field:
   ```toml
   version = "1.6.0"
   ```
   Update to the same value, e.g. `"1.7.0"`.

3. `auto_lowpoly_baker/CHANGELOG.md` — add a new section at the top under `# Changelog`:
   ```markdown
   ## 1.7.0

   - <one bullet per user-facing change, imperative and specific>
   ```

Do **not** touch `auto_lowpoly_baker/build_info.py` — the build counter there is managed by
the build script.

## Steps

1. Read the current version from `blender_manifest.toml` and confirm `__init__.py` matches.
   If they already disagree, fix the drift first (treat the manifest as the source of truth).
2. Determine the new version from the policy above based on what changed.
3. Edit the `bl_info` tuple in `__init__.py` and the `version` string in
   `blender_manifest.toml` to the new version — they must be identical.
4. Add a `## <new version>` section to the top of `CHANGELOG.md` describing the changes.
5. Verify the package still compiles:
   ```bash
   python -m py_compile auto_lowpoly_baker/__init__.py
   ```
6. Build the ZIP (this also auto-increments the build counter shown in the panel title):
   ```bash
   python scripts/build_zip.py
   ```
7. Reinstall into the local Blender (uninstall the old copy, install and enable the new
   build). See **Reinstall into Blender** below:
   ```bash
   python scripts/reinstall.py
   ```
8. Report the old -> new version, the CHANGELOG bullets, the build number printed by the
   build script, and whether the reinstall succeeded.

## Reinstall into Blender

`scripts/reinstall.py` finds `blender.exe` and runs `scripts/install_blender.py` inside
Blender (background mode) to remove any previously installed copy, install
`dist/auto_lowpoly_baker.zip`, enable it, and save preferences. It handles both the Blender
4.2+ extensions API and the legacy add-on API.

Before running the reinstall:

- **Close the Blender GUI.** An open instance can overwrite the saved preferences when it
  exits, and it will not see the new build until it is restarted anyway.
- If auto-detection fails, set the Blender executable path first, for example:
  ```bash
  set BLENDER_EXE="C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
  ```

After a successful reinstall, tell the user to reopen Blender to use the new build. If the
user only wants to build (not reinstall), skip step 7.

## Verify

- `__init__.py` tuple and `blender_manifest.toml` string are the exact same version.
- `CHANGELOG.md` has a matching top entry.
- `python scripts/build_zip.py` printed `Built ... (build N)` with no error.
- `python scripts/reinstall.py` printed `Reinstall complete.` (the Blender log lines are
  prefixed with `[reinstall]`); a non-zero exit means the install could not be completed.
  The install pass ends with `ok: enable bl_ext.user_default.auto_lowpoly_baker`. A single
  transient `Add-on not loaded: "auto_lowpoly_baker"` line during that pass is expected and
  harmless — it is Blender booting between the uninstall and install passes, and it
  self-heals on the final prefs save. A normal Blender launch afterwards is error-free.
